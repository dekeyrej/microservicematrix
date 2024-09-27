""" ... """
# import json
from typing import Union
from pages.serverpage import ServerPage
import arrow

number = Union[float, int]

class OWMServer(ServerPage):
    """ ... """
    def __init__(self, prod, period, path: str=None):
        super().__init__(prod, period, path)
        self.type = 'Weather'
        self.url = f'https://api.openweathermap.org/data/3.0/onecall?appid=' \
                   f'{self.secrets["owmkey"]}&lat={self.secrets["latitude"]}&' \
                   f'lon={self.secrets["longitude"]}' \
                   f'&exclude=minutely,alerts&units=imperial&lang=en'
        print(self.url)
        self.clear_secrets()
        self.dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE',
                     'S','SSW','SW','WSW','W','WNW','NW','NNW']

    def update(self):
        """ ... """
        tnow = arrow.now().to('US/Eastern')
        jstuff = self.fetch(self.url,'Fetching Weather',self.now_str(tnow,True))
        if jstuff is not None:
            data = {}
            data['type'] = 'Weather'
            data['updated'] = self.now_str(tnow,False)
            data['valid']   = self.now_str(tnow.shift(seconds=+self.update_period),True)
            data['values'] = {}
# current weather
            data['values']["current"] = {}
            data['values']["current"]["temp"]= \
                float(jstuff["current"]["temp"])  # "{:.1f}°F".format(temp)
            data['values']["current"]["fl"]        = float(jstuff["current"]["feels_like"])
            data['values']["current"]["humid"]     = int(jstuff["current"]["humidity"])
            data['values']["current"]["windDir"]   = \
                self.deg_to_dir(int(jstuff["current"]["wind_deg"]))
            data['values']["current"]["windSpeed"] = float(jstuff["current"]["wind_speed"])
            try:
                data['values']["current"]["windGust"]  = float(jstuff["current"]["wind_gust"])
            # except KeyError as err:
            except KeyError:
                # print(f"Fetching Weather No {err} error occurred @ {self.now_str(tnow)}")
                data['values']["current"]["windGust"]  = 0.0
            data['values']["current"]["desc"]      = jstuff["current"]["weather"][0]["description"]
            icon = jstuff["current"]["weather"][0]["icon"]
            data['values']["current"]["dn"] = icon[2]
            wid  = int(str(jstuff["current"]["weather"][0]["id"]))
            data['values']["current"]["wid"] = wid
            data['values']["current"]["nwid"]    = self.to_nwid(icon, wid)
# forecast weather
            data['values']["forecast"] = []
            for i in range(0,8):
                if i == 0:
                    dow = 'TOD'
                elif i == 1:
                    dow = 'TOM'
                else:
                    dow = tnow.shift(days=+i).format('ddd').upper()
                high = int(jstuff["daily"][i]["temp"]["max"])
                low = int(jstuff["daily"][i]["temp"]["min"])
                icon = jstuff["daily"][i]["weather"][0]["icon"]
                wid  = int(str(jstuff["daily"][i]["weather"][0]["id"]))
                nwid = self.to_nwid(icon,wid)
                data['values']["forecast"].append({"dow" : dow, "dn": icon[2], "wid": wid,
                                                   "nwid": nwid, "high": high, "low": low})
# hourly weather
            data['values']["hourly"] = []
            for i in range(0,48):
                tnow = \
                    arrow.Arrow.fromtimestamp(float(jstuff["hourly"][i]["dt"]),
                                              tzinfo='US/Eastern')
                hour  = tnow.format('HH:mm')
                temp = int(jstuff["hourly"][i]["temp"])
                feel = int(jstuff["hourly"][i]["feels_like"])
                icon = jstuff["hourly"][i]["weather"][0]["icon"]
                wid  = int(str(jstuff["hourly"][i]["weather"][0]["id"]))
                nwid = self.to_nwid(icon, wid)
                data['values']["hourly"].append({"hour": hour, "dn": icon[2], "wid": wid, 
                                                 "nwid": nwid, "temp": temp, "feel": feel})

            # self.mongoWrite(data, 'Weather')
            self.dba.write(data)
            print(f'{type(self).__name__} updated.')
            # self.log('{} updated.'.format(type(self).__name__))

    def to_nwid(self, icon: str, wid: int) -> int:
        """ ... """
        # print(f'Icon: {icon}, WeatherID: {wid}')
        if ((icon[2] == "n") and          # icon[2] # returns "d" for day, or "n" for night
            wid in (800, 801, 802, 951)): # these four WeatherIDs have a unique night icon
            nwid = wid + 61000
        else:
            nwid = wid + 60000
        return nwid

    def deg_to_dir(self, deg: number) -> str:
        """ ... """
        return self.dirs[round(deg/22.5) % 16]

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
        OWMServer(True, 907).run()
    else:
        OWMServer(False, 907, SECRETS_PATH).run()
