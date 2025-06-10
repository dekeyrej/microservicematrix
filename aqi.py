""" ... """
import json

import arrow

from plain_pages.serverpage import ServerPage

"""
From https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf
(note: this is declared _outside_ the AQIServer context)
"""
aqidata = {
    "aqi": {"adjectives": ["Good",      "Moderate",    "Unhealthy for Sensitive Groups", "Unhealthy", "Very Unhealthy", "Hazardous"],
            "colors" :    ["(0,228,0)", "(255,255,0)", "(255,126,0)",                    "(255,0,0)", "(143,63,151)",   "(126,0,35)"],
            "values":     [ (0,50),      (51,100),      (101,150),                        (151,200),   (201,300),        (301,500)]},
    "pollutants": {
        "o3":    {"name": "Ozone", "weight": 47.998, "units": "ppb", "decimals": 0,
                    "values": [(0,54), (55,70), (71,85), (86,105), (106,200), (201,500)]}, 
        "pm2_5": {"name": "Particulate Matter (2.5 microns)", "weight": 1, "units": "ug/m3", "decimals": 1,
                    "values": [(0,12), (12.1,35.4), (35.5,55.4), (55.5,150.4), (150.5,250.4), (250.5,500.4)]}, 
        "pm10":  {"name": "Particulate Matter (10 microns)", "weight": 1, "units": "ug/m3", "decimals": 0,
                    "values": [(0,54), (55,154), (155,254), (255,354), (355,424), (425,604)]}, 
        "co":    {"name": "Carbon Monoxide", "weight": 28.01, "units": "ppm",   "decimals": 1,
                    "values": [(0,4.4), (4.5,9.4), (9.5,12.4), (12.5,15.4), (15.5,30.4), (30.5,50.4)]}, 
        "so2":   {"name": "Sulfur Dioxide", "weight": 64.065, "units": "ppb",   "decimals": 0,
                    "values": [(0,35), (36,75), (76,185), (186,304), (305,604), (605,1004)]}, 
        "no2":   {"name": "Nitrogen Dioxide", "weight": 46.006, "units": "ppb",   "decimals": 0,
                    "values": [(0,53), (54,100), (101,360), (361,649), (650,1249), (1250,2049)]}
    }
}


class AQIServer(ServerPage):
    """ ... """
    def __init__(self, prod, period, secretcfg, secretdef):
        super().__init__(prod, period, secretcfg, secretdef)
        self.type = 'AQI'
        self.url = f'https://api.openweathermap.org/data/2.5/air_pollution?appid=' \
                   f'{self.secrets["owmkey"]}&lat={self.secrets["latitude"]}&' \
                   f'lon={self.secrets["longitude"]}'
        del self.secrets
        # self.clear_secrets()

    def update(self):
        """ ... """
        tnow = arrow.now().to(self.timezone)
        jstuff = self.fetch(self.url, 'Fetching Air Pollution', self.now_str(tnow, True))
        if jstuff is not None:
            utc_measurement_time = arrow.get(str(jstuff['list'][0]['dt']), 'X')
            
            max_score = 0
            max_row = 0
            max_pollutant = ""
            # loop through the pollutants and find the max score
            for pollutant in aqidata['pollutants'].keys():
                raw_value = jstuff["list"][0]["components"][pollutant]
                converted_value = self.convert_reading(raw_value, pollutant)
                scaled_value, row = self.scaled_reading(converted_value, pollutant)
                if scaled_value > max_score:
                    max_score = scaled_value
                    max_row = row
                    max_pollutant = pollutant

            data = {
                'type': self.type,
                'updated': self.now_str(tnow, False),
                'valid': self.now_str(tnow.shift(seconds=self.update_period), True),
                'values': {
                    'date_time': utc_measurement_time.to(self.timezone).format('MM/DD/YYYY h:mm A ZZZ'),
                    'aqi_score': max_score,
                    'aqi_adjective': aqidata["aqi"]["adjectives"][max_row],
                    'color': aqidata["aqi"]["colors"][max_row],
                    'main_pollutant': aqidata["pollutants"][max_pollutant]["name"]
                }
            }

            # write out the results
            self.dba.write(data)
            # print(f'{type(self).__name__} updated.')

    def convert_reading(self, val: float|int, pol: str) -> float|int:
        """
        Values delivered by OWM are all in micrograms per cubic meter.
        function (1) converts to ppm or ppb, and
                (2) returns the correct significant digits
        """
        units    = aqidata['pollutants'][pol]["units"]
        decimals = aqidata['pollutants'][pol]["decimals"]
        weight   = aqidata['pollutants'][pol]["weight"]

        if units == "ppm":
            conversion = 24.45 / (weight * 1000)
        elif units == "ppb":
            conversion = 24.45 / weight
        elif units == "ug/m3":
            conversion = 1

        if decimals == 0:
            return int(round(val * conversion * 10**decimals, 0)/10**decimals)

        return round(val * conversion * 10**decimals, 0)/10**decimals

    def scaled_reading(self, cval: float|int, pol: str) -> int:
        """
        function scales the converted value based on the pollutants 'Break Points'
        and returns the (AQI) scaled value and the row in the table (AQI Level).
        https://www.airnow.gov/sites/default/files/
                 2020-05/aqi-technical-assistance-document-sept2018.pdf
        """
        aq = aqidata['aqi']['values']
        pm = aqidata['pollutants'][pol]['values']
        scaled = 0
        row = 0
        for i in range(6):
            if pm[i][0] <= cval <= pm[i][1]:
                row = i
                scaled = int(round((cval - pm[i][0]) * (aq[i][1] - aq[i][0])/
                                                       (pm[i][1] - pm[i][0]) + aq[i][0],0))
                return scaled, row
        return scaled, row

if __name__ == '__main__':
    import os

    try:
        PROD = os.environ["PROD"]
    except KeyError:
        pass

    if PROD == '1':
        import config as cfg
        secretcfg = cfg.secretcfg
        secretdef = cfg.secretdef
        AQIServer(True, 919, cfg.secretcfg, cfg.secretdef).run()
    else:
        import devconfig as cfg
        secretcfg = cfg.secretcfg
        secretdef = cfg.secretdef
        AQIServer(False, 919, cfg.secretcfg, cfg.secretdef).run()

