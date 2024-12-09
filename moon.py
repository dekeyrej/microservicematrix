""" Sun and Moon data server """
import math
from typing import Mapping
import arrow
import json

from pages.serverpage import ServerPage
# from secretsecrets import encsecrets

class MoonServer(ServerPage):
    """ subclass of ServerPage to fetch sun and moon data """
    def __init__(self, prod, period, path: str=None):
        super().__init__(prod, period, path)
        self.headers = {'User-Agent': 'moon.py joedekeyrel@gmail.com'}
        self.type = 'Moon'
        self.loc_str = f'lat={self.secrets["latitude"]}&lon={self.secrets["longitude"]}'
        self.timezone = self.secrets['timezone'] # not currently used
        self.clear_secrets()
        self.twelve_hour = True

    def update(self):
        """ 
        fetch web data and update database 
        as of 9/1/2023, Norwegian Met updated its API to version 3.0
        """
        updtp = self.update_period
        tnow = arrow.now().to('US/Eastern')
        today, tomorrow, tstmp = self.url_date_str()
        urls = []
        urls.append('https://api.met.no/weatherapi/sunrise/3.0/sun?' + self.loc_str + today)
        urls.append('https://api.met.no/weatherapi/sunrise/3.0/sun?' + self.loc_str + tomorrow)
        urls.append('https://api.met.no/weatherapi/sunrise/3.0/moon?' + self.loc_str + today)
        urls.append('https://api.met.no/weatherapi/sunrise/3.0/moon?' + self.loc_str + tomorrow)
        respcount = 0
        responses = []
        for i in range(4):
            resp = self.fetch(urls[i],'Fetching Moon/Sun',tnow.format('MM/DD/YYYY hh:mm A ZZZ'), headers=self.headers)
            if resp is not None: 
                # print(f'response from url:{urls[i]} is [{resp}]')
                responses.append(resp)
                respcount += 1

        if respcount == 4:
            sun_data = [
                responses[i]['properties'] for i in range(2)
            ]

            moon_data = [
                responses[i]['properties'] for i in range(2,4)
            ]
            phase, illumstr = self.moon_condition(moon_data[0]['moonphase'])

            data = {
                'type': 'Moon',
                'updated': tnow.format('MM/DD/YYYY h:mm A ZZZ'),
                'valid': tnow.shift(seconds=+updtp).format('MM/DD/YYYY h:mm:ss A ZZZ'),
                'values': {
                    'phase': phase,
                    'illumstr': illumstr,
                    'sunevent': self.sun_event(sun_data, tstmp),
                    'moonevent': self.moon_event(moon_data)
                }
            }
            
            self.dba.write(data)
            # print(json.dumps(data['values'], indent=1))
            print(f'{type(self).__name__} updated.')

    def moon_condition(self, moonphase: float) -> tuple[int, float]:
        """ convert moonphase to an integer phase (index of phase image) and an illumination %
            moonphase values seem to be in the range 0.0..359.99
        """
        phase     =              int(moonphase / 3.6 ) % 100  # => 0..99
        illum     = self.age_to_illum(moonphase / 360)        # => 0.0..1.0
        return phase, illum

    def sun_event(self, mnd: Mapping, tstmp) -> str:
        """ determine the next sun event (sunrise or sunset) """
        # sunrise and sunset happen every day - easier
        sunrise   = self.parse_time(mnd[0]['sunrise']['time'])
        sunset    = self.parse_time(mnd[0]['sunset']['time'])
        tomorrow_sunrise = self.parse_time(mnd[1]['sunrise']['time'])
        # determine which sun event is next
        # print(type(tstmp))
        # print(type(sunrise))
        if tstmp <= sunrise:
            event = f"Sunrise:  {self.ts2hhmm(sunrise)}"
        elif tstmp <= sunset:
            event = f"Sunset:   {self.ts2hhmm(sunset)}"
        else:
            event = f"Sunrise:  {self.ts2hhmm(tomorrow_sunrise)}"
        return event

    def moon_event(self, mnd: Mapping) -> str:
        """Determine the next moon event (moonrise or moonset)"""
        events = []

        for day in mnd[:2]:
            if 'moonrise' in day and day['moonrise']['time'] is not None:
                moon_rise = self.parse_time(day['moonrise']['time'])
                events.append(('Rise', moon_rise))
            if 'moonset' in day and day['moonset']['time'] is not None:
                moon_set = self.parse_time(day['moonset']['time'])
                events.append(('Set', moon_set))

        # Sort the events by time and find the next event
        events.sort(key=lambda e: e[1])
        current_time = arrow.now().format('X')

        for event_type, event_time in events:
            if event_time > current_time:
                next_event = (event_type, event_time)
                break

        event_str = f"Moonrise: {self.ts2hhmm(next_event[1])}" if next_event[0] == 'Rise' else f"Moonset:  {self.ts2hhmm(next_event[1])}"
        return event_str

    def age_to_illum(self, age: int) -> float:
        """ convert age (0..100) to a percent illumination """
        if age <= 0.5:
            illum = (1 - math.cos(age * 2 * math.pi)) * 50
        else:
            illum = (1 + math.cos((age - 0.5) * 2 * math.pi)) * 50
        return f'{illum:.1f}%'

    def url_date_str(self) -> tuple[str, str, str]:
        """ convert 'now' into three strings:
            today's date,
            tomorrow's date, and
            a unix timestamp
        """
        tnow = arrow.now().to('US/Eastern')
        today = tnow.format('[&date=]YYYY-MM-DD[&offset=]ZZ')
        tomorrow = tnow.shift(days=+1).format('[&date=]YYYY-MM-DD[&offset=]ZZ')
        return today, tomorrow, tnow.format('X')

    def parse_time(self, timestr: str) -> arrow:
        """ converts a timestamp string into an arrow (a string?) """
        return arrow.get(timestr).format('X')

    def ts2hhmm(self, tstmp: str) -> str:
        """ converts a timestamp into an arrow and returns either a
            12-hr time, or a 24-hr time
        """
        tnow = arrow.get(tstmp,'X').to('US/Eastern')
        if self.twelve_hour:
            out = tnow.format('hh:mm A')
        else:
            out = tnow.format('HH:mm')
        return out

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
        MoonServer(True, 3607).run()
    else:
        MoonServer(False, 3607, SECRETS_PATH).run()
