""" Reads (google) calendar events for today """
import json
import arrow

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from microservice import MicroService

class CalendarServer(MicroService):
    """ Subclass of serverpage for reading calendar events """
    def __init__(self, period, secretcfg, secretdef):
        super().__init__(period, secretcfg, secretdef)
        self.type = 'Calendar'
#       calendar has to be public :-/
        self._base_calendar_url = f'https://www.googleapis.com/calendar/v3/calendars/' \
            f'{self.secrets["google_calendar_id"]}/events?key={self.secrets["google_api_key"]}' \
            f'&orderBy=starttime&singleEvents=true'
        del self.secrets
        self._url = None

    def update(self):
        """ called by ServerPage.check() """
#         t = datetime.datetime(2022,10,6,14,0,0)  ## jammed date/time for testing
        tnow = arrow.now().to(self.timezone)
        time_min = tnow.replace(hour=6, minute=0, second=0).format("YYYY-MM-DDTHH:mm:ssZZ")
        time_max = tnow.replace(hour=20, minute=0, second=0).format("YYYY-MM-DDTHH:mm:ssZZ")
        self._url = self._base_calendar_url + f"&timeMin={time_min}&timeMax={time_max}"
        resp = self.fetch(self._url,'Fetching Calendar',tnow.format('MM/DD/YYYY hh:mm A ZZZ'))
        if resp is not None:
            items = resp['items']
            data = {
                'type': self.type,
                'updated': tnow.format('MM/DD/YYYY h:mm A Z'),
                'valid': tnow.shift(seconds=self.update_period).format('MM/DD/YYYY h:mm:ss A Z'),
                'values': [(item["summary"], item["start"]["dateTime"], item["end"]["dateTime"]) for item in items]
            }
            if len(data['values']) == 0:
                data['values'].append(('No events'))
            logging.info(json.dumps(data,indent=2))
            self.r.publish('update', json.dumps(data))
            logging.debug(json.dumps(data, indent=2))
            logging.info(f'{type(self).__name__} updated.')

if __name__ == '__main__':
    import os

    period = int(os.environ.get("PERIOD", '600'))

    with open("secretcfg.json") as f:
        secretcfg = json.load(f)

    with open("secretdef.json") as f:
        secretdef = json.load(f)

    logging.debug(f"Starting Events Server with period: {period},\nsecrets type: {secretcfg}, and\nsecret definition: {secretdef}")

    CalendarServer(period, secretcfg, secretdef).run()
