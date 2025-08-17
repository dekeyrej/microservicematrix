""" ... """
import json
import arrow
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from microservice import MicroService

class OWMServer(MicroService):
    """ ... """
    def __init__(self, period, secretcfg, secretdef):
        super().__init__(period, secretcfg, secretdef)
        self.type = 'Weather'
        self.url = f'https://api.openweathermap.org/data/3.0/onecall?appid=' \
                   f'{self.secrets["owmkey"]}&lat={self.secrets["latitude"]}&' \
                   f'lon={self.secrets["longitude"]}' \
                   f'&exclude=minutely,alerts&units=imperial&lang=en'
        logging.debug(self.url)
        del self.secrets
        self.dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE',
                     'S','SSW','SW','WSW','W','WNW','NW','NNW']

    def update(self):
        tnow = arrow.now().to(self.timezone)
        jstuff = self.fetch(self.url, 'Fetching Weather', self.now_str(tnow, True))
        if jstuff is not None:
            data = {
                'type': 'Weather',
                'updated': self.now_str(tnow, False),
                'valid': self.now_str(tnow.shift(seconds=self.update_period), True),
                'values': {
                    'current': {
                        'temp': float(jstuff["current"]["temp"]),
                        'fl': float(jstuff["current"]["feels_like"]),
                        'humid': int(jstuff["current"]["humidity"]),
                        'windDir': self.deg_to_dir(int(jstuff["current"]["wind_deg"])),
                        'windSpeed': float(jstuff["current"]["wind_speed"]),
                        'windGust': float(jstuff["current"].get("wind_gust", 0.0)),
                        'desc': jstuff["current"]["weather"][0]["description"],
                        'dn': jstuff["current"]["weather"][0]["icon"][2],
                        'wid': int(jstuff["current"]["weather"][0]["id"]),
                        'nwid': self.to_nwid(jstuff["current"]["weather"][0]["icon"], int(jstuff["current"]["weather"][0]["id"]))
                    },
                    'forecast': [
                        {
                            'dow': 'TOD' if i == 0 else 'TOM' if i == 1 else tnow.shift(days=i).format('ddd').upper(),
                            'dn': jstuff["daily"][i]["weather"][0]["icon"][2],
                            'wid': int(jstuff["daily"][i]["weather"][0]["id"]),
                            'nwid': self.to_nwid(jstuff["daily"][i]["weather"][0]["icon"], int(jstuff["daily"][i]["weather"][0]["id"])),
                            'high': int(jstuff["daily"][i]["temp"]["max"]),
                            'low': int(jstuff["daily"][i]["temp"]["min"])
                        } for i in range(8)
                    ],
                    'hourly': [
                        {
                            'hour': arrow.Arrow.fromtimestamp(float(jstuff["hourly"][i]["dt"]), tzinfo='US/Eastern').format('HH:mm'),
                            'dn': jstuff["hourly"][i]["weather"][0]["icon"][2],
                            'wid': int(jstuff["hourly"][i]["weather"][0]["id"]),
                            'nwid': self.to_nwid(jstuff["hourly"][i]["weather"][0]["icon"], int(jstuff["hourly"][i]["weather"][0]["id"])),
                            'temp': int(jstuff["hourly"][i]["temp"]),
                            'feel': int(jstuff["hourly"][i]["feels_like"])
                        } for i in range(48)
                    ]
                }
            }
            self.r.publish('update', json.dumps(data))
            logging.info(f'{type(self).__name__} updated.')


    def to_nwid(self, icon: str, wid: int) -> int:
        """ ... """
        # print(f'Icon: {icon}, WeatherID: {wid}')
        if ((icon[2] == "n") and          # icon[2] # returns "d" for day, or "n" for night
            wid in (800, 801, 802, 951)): # these four WeatherIDs have a unique night icon
            nwid = wid + 61000
        else:
            nwid = wid + 60000
        return nwid

    def deg_to_dir(self, deg) -> str:
        """ ... """
        return self.dirs[round(deg/22.5) % 16]

if __name__ == '__main__':
    import os

    period = int(os.environ.get("PERIOD", '600'))

    with open("secretcfg.json") as f:
        secretcfg = json.load(f)

    with open("secretdef.json") as f:
        secretdef = json.load(f)

    logging.debug(f"Starting Events Server with period: {period},\nsecrets type: {secretcfg}, and\nsecret definition: {secretdef}")

    OWMServer(period, secretcfg, secretdef).run()
