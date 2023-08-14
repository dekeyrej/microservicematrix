""" Sun and Moon data server """
import math
from typing import Mapping
import arrow
# import json

from pages.serverpage import ServerPage
# from secretsecrets import encsecrets

class MoonServer(ServerPage):
    """ subclass of ServerPage to fetch sun and moon data """
    def __init__(self, prod, period, path: str=None):
        super().__init__(prod, period, path)
        self.type = 'Moon'
        self.loc_str = f'lat={self.secrets["latitude"]}&lon={self.secrets["longitude"]}'
        self.timezone = self.secrets['timezone'] # not currently used
        self.clear_secrets()
        self.twelve_hour = True

    def update(self):
        """ fetch web data and update database """
        updtp = self.update_period
        tnow = arrow.now().to('US/Eastern')
        today, tomorrow, tstmp = self.url_date_str()
        url = ['https://api.met.no/weatherapi/sunrise/2.0/.json?' + self.loc_str + today]
        url.append('https://api.met.no/weatherapi/sunrise/2.0/.json?' + self.loc_str + tomorrow)
        responsea = self.fetch(url[0],'Fetching Moon/Sun',tnow.format('MM/DD/YYYY hh:mm A ZZZ'))
        responseb = self.fetch(url[1],'Fetching Moon/Sun',tnow.format('MM/DD/YYYY hh:mm A ZZZ'))
        if responsea is not None and responseb is not None:
            data = {}
            data['type'] = 'Moon'
            data['updated'] = tnow.format('MM/DD/YYYY h:mm A ZZZ')
            data['valid'] = tnow.shift(seconds=+updtp).format('MM/DD/YYYY h:mm:ss A ZZZ')
            data['values'] = {}

            moon_data = [responsea['location']['time'][0]]
            moon_data.append(responseb['location']['time'][0])

            data['values']['phase'], data['values']['illumstr'] = self.moon_condition(moon_data)
            # print(tstmp)
            data['values']['sunevent']  = self.sun_event(moon_data, tstmp)
            data['values']['moonevent'] = self.moon_event(moon_data)
            self.dba.write(data)
            print(f'{type(self).__name__} updated.')

    def moon_condition(self, mnd: Mapping) -> (int, float):
        """ parse out the current moon condition """
        # Reconstitute JSON data into the elements we need
        phase     = int(float(mnd[0]['moonphase']['value'])) % 100
        illum     = self.age_to_illum(float(mnd[0]['moonphase']['value']) / 100)
        # midnight  = self.parse_time(md[0]['moonphase']['time'])
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
        """ determine the next moon event (moonrise or moonset) """
        # moonrise and/or moonset may not occur in the current day
        #   so check today
        events = []
        if 'moonrise' in mnd[0]:
            rise = self.parse_time(mnd[0]['moonrise']['time'])
            events.append(('Rise',rise))
        else:
            rise = None
        if 'moonset' in mnd[0]:
            mset = self.parse_time(mnd[0]['moonset']['time'])
            events.append(('Set',mset))
        else:
            mset = None
        #   and check tomorrow
        if 'moonrise' in mnd[1]:
            rise = self.parse_time(mnd[1]['moonrise']['time'])
            events.append(('Rise',rise))
        else:
            rise = None  # was self.rise???
        if 'moonset' in mnd[1]:
            mset = self.parse_time(mnd[1]['moonset']['time'])
            events.append(('Set',mset))
        else:
            mset = None

        # is the moon risen or set? What event is 'next' - a set, or a rise?
        # sort the events by time, see which one is next
        events.sort(reverse=False, key=lambda e : e[1]) # e[1] is the event time
        rfn = arrow.now().format('X')
        for evt in events:
            if evt[1] > rfn:
                next_event = evt
                break
        if next_event[0] == 'Rise':
            event = f"Moonrise: {self.ts2hhmm(next_event[1])}"
        else:
            event = f"Moonset:  {self.ts2hhmm(next_event[1])}"
        return event

    def age_to_illum(self, age: int) -> float:
        """ convert age (0..100) to a percent illumination """
        if age <= 0.5:
            illum = (1 - math.cos(age * 2 * math.pi)) * 50
        else:
            illum = (1 + math.cos((age - 0.5) * 2 * math.pi)) * 50
        return f'{illum:.1f}%'

    def url_date_str(self) -> (str, str, str):
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
        MoonServer(True, 911).run()
    else:
        MoonServer(False, 911, SECRETS_PATH).run()
