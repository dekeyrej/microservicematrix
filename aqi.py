""" ... """
from typing import Union
import json

import arrow
import pandas as pd

from pages.serverpage import ServerPage

numtype = Union[float, int]

class AQIServer(ServerPage):
    """ ... """
    def __init__(self, prod: bool, period: int, path: str=None):
        super().__init__(prod, period, path)
        self.type = 'AQI'
        self.url = f'https://api.openweathermap.org/data/2.5/air_pollution?appid=' \
                   f'{self.secrets["owmkey"]}&lat={self.secrets["latitude"]}&' \
                   f'lon={self.secrets["longitude"]}'
        self.clear_secrets()
        self.load_data()
        self.daf = pd.DataFrame(self.aqidata, index = self.dfindex)

    def load_data(self):
        cmap = self.ks.read_map('default', 'aqi-data')
        self.aqidata = json.loads(cmap.data['aqidata'])
        self.pollutants = json.loads(cmap.data['pollutants'])
        self.pollutant_measures = json.loads(cmap.data['pollutant_measures'])
        self.dfindex = json.loads(cmap.data['dfindex'])
        

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
            dts = arrow.get(str(jstuff['list'][0]['dt']), 'X')
            data['values']['dt'] = dts.to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
            # loop through the readings
            maxscore = 1
            maxrow = "1"
            maxpol = ""
            index = 0
            for pol in self.pollutants:
                raw = jstuff["list"][0]["components"][pol]
                converted = self.convert_reading(raw, pol)
                scaled, row = self.scaled_reading(converted, pol)
                if scaled > maxscore:
                    maxscore = scaled
                    maxrow = row
                    maxpol = pol
                # print(f'{p} - raw: {raw}, converted: {converted}, scaled: {scaled} on row {row}')
                index += 1

            print(f'AQI: {maxscore} ({self.daf.at[maxrow,"aqi_adjective"]} -' \
                  f'{self.daf.at[maxrow,"aqi_color"]}) '\
                  f'with {self.pollutant_measures[maxpol]["name"]} as the main factor.')
            data['values']['aqi_score'] = maxscore
            data['values']['aqi_adjective'] = self.daf.at[maxrow,"aqi_adjective"]
            data['values']['color'] = self.daf.at[maxrow,"aqi_color"]
            data['values']['main_pollutant'] = self.pollutant_measures[maxpol]["name"]
            # write out the results
            self.dba.write(data)
            # print(f'{type(self).__name__} updated.')

    def convert_reading(self, val: numtype, pol: str) -> numtype:
        """ 
        Values delivered by OWM are all in micrograms per cubic meter.
        function (1) converts to ppm or ppb, and
                (2) returns the correct significant digits
        """
        units = self.pollutant_measures[pol]["units"]
        decimals = self.pollutant_measures[pol]["decimals"]
        weight = self.pollutant_measures[pol]["weight"]

        if units == "ppm":
            conversion = 24.45 / (weight * 1000)
        elif units == "ppb":
            conversion = 24.45 / weight
        elif units == "ug/m3":
            conversion = 1

        if decimals == 0:
            return int(round(val * conversion * 10**decimals, 0)/10**decimals)

        return round(val * conversion * 10**decimals, 0)/10**decimals

    def scaled_reading(self, cval: numtype, pol: str) -> int:
        """
        function scales the converted value based on the pollutants 'Break Points'
        and returns the (AQI) scaled value and the row in the table (AQI Level).
        https://www.airnow.gov/sites/default/files/
                 2020-05/aqi-technical-assistance-document-sept2018.pdf
        """
        aql = 'aqi_low'
        aqh = 'aqi_high'
        pml =  f'{pol}_low'
        pmh = f'{pol}_high'
        scaled = 1
        row = '1'
        for i in self.dfindex:
            if self.daf.at[i, pml] <= cval <= self.daf.at[i, pmh]:
                row = i
                scaled = int(round((cval - self.daf.at[i, pml])* (self.daf.at[i, aqh] -
                                                                 self.daf.at[i, aql])/
                                   (self.daf.at[i, pmh] -
                                    self.daf.at[i, pml]) + self.daf.at[i, aql],0))
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
