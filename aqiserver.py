""" ... """
import json
from typing import Union

import arrow
import pandas as pd

from aqi_data import aqidata, pollutants, pollutant_measures, dfindex

from pages.serverpage import ServerPage

number = Union[float, int]

class AQIServer(ServerPage):
    """ ... """
    def __init__(self, prod: bool, period: int, path: str=None):
        super().__init__(prod, period, path)
        self.type = 'AQI'
        self.url = f'https://api.openweathermap.org/data/2.5/air_pollution?appid=' \
                   f'{self.secrets["owmkey"]}&lat={self.secrets["latitude"]}&' \
                   f'lon={self.secrets["longitude"]}'
        self.clear_secrets()
        self.df = pd.DataFrame(aqidata, index = dfindex)

    def update(self):
        """ ... """
        tnow = arrow.now().to('US/Eastern')
        jstuff = self.fetch(self.url,'Fetching Air Pollution',self.now_str(tnow,True))
        if jstuff is not None:
            # print(json.dumps(jstuff, indent=2))
            data = {}
            data['type'] = self.type
            data['updated'] = self.now_str(tnow,False)
            data['valid']   = self.now_str(tnow.shift(seconds=+self.update_period),True)
            data['values'] = {}
            data['values']['dt'] = arrow.get(str(jstuff['list'][0]['dt']), 'X').to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
            # loop through the readings
            maxscore = 1
            maxrow = "1"
            maxpol = ""
            index = 0
            for p in pollutants:
                raw = jstuff["list"][0]["components"][p]
                converted = self.convert_reading(raw, p)
                scaled, row = self.scaled_reading(converted, p)
                if scaled > maxscore:
                    maxscore = scaled
                    maxrow = row
                    maxpol = p
                # print(f'{p} - raw: {raw}, converted: {converted}, scaled: {scaled} on row {row}')
                index += 1

            print(f'AQI: {maxscore} ({self.df.at[maxrow,"aqi_adjective"]} - {self.df.at[maxrow,"aqi_color"]}) with {pollutant_measures[maxpol]["name"]} as the main factor.')
            data['values']['aqi_score'] = maxscore
            data['values']['aqi_adjective'] = self.df.at[maxrow,"aqi_adjective"]
            data['values']['color'] = self.df.at[maxrow,"aqi_color"]
            data['values']['main_pollutant'] = pollutant_measures[maxpol]["name"]
            # write out the results
            self.dba.write(data)
            # print(f'{type(self).__name__} updated.')

    def convert_reading(self, val: number, pol: str) -> number:
        """ 
        Values delivered by OWM are all in micrograms per cubic meter.
        function (1) converts to ppm or ppb, and
                (2) returns the correct significant digits
        """
        units = pollutant_measures[pol]["units"]
        decimals = pollutant_measures[pol]["decimals"]
        weight = pollutant_measures[pol]["weight"]
        
        if units == "ppm":
            conversion = 24.45 / (weight * 1000)
        elif units == "ppb":
            conversion = 24.45 / weight
        elif units == "ug/m3":
            conversion = 1
        
        if decimals == 0:
            return int(round(val * conversion * 10**decimals, 0)/10**decimals)
        else:
            return round(val * conversion * 10**decimals, 0)/10**decimals

    def scaled_reading(self, cval: number, pol: str) -> int:
        """
        function scales the converted value based on the pollutants 'Break Points'
        and returns the (AQI) scaled value and the row in the table (AQI Level).
        Derived from https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
        """
        al = 'aqi_low'
        ah = 'aqi_high'
        pl =  f'{pol}_low'
        ph = f'{pol}_high'
        scaled = 1
        row = '1'
        for i in dfindex:
            if self.df.at[i, pl] <= cval <= self.df.at[i, ph]:
                row = i
                # print(f'{cval} is between {self.df.at[i, pl]} and {self.df.at[i, ph]} on row {row}')
                scaled = int(round((cval - self.df.at[i, pl])* (self.df.at[i, ah] - self.df.at[i, al])/(self.df.at[i, ph] - self.df.at[i, pl]) + self.df.at[i, al],0))
                return scaled, row
        return scaled, row

if __name__ == '__main__':
    import os
    import dotenv
    
    dotenv.load_dotenv()

    try:
        PROD = os.environ["PROD"]
        SECRETS_PATH = os.environ["SECRETS_PATH"]
    except KeyError:
        pass
    
    if PROD == '1':
        AQIServer(True, 919).run()
    else:
        AQIServer(False, 919, SECRETS_PATH).run()
