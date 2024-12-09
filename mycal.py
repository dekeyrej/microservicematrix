""" Reads (google) calendar events for today """
# import json
import arrow

from pages.serverpage import ServerPage


class CalendarServer(ServerPage):
    """ Subclass of serverpage for reading calendar events """
    def __init__(self, prod, period, path: str=None):
        super().__init__(prod, period, path)
        self.type = 'Calendar'
#       calendar has to be public :-/
        self._base_calendar_url = f'https://www.googleapis.com/calendar/v3/calendars/' \
            f'{self.secrets["google_calendar"]}/events?key={self.secrets["google_api_key"]}' \
            f'&orderBy=starttime&singleEvents=true'
        self.clear_secrets()
        self._url = None

    def update(self):
        """ called by ServerPage.check() """
#         t = datetime.datetime(2022,10,6,14,0,0)  ## jammed date/time for testing
        tnow = arrow.now().to('US/Eastern')
        time_min = tnow.replace(hour=6, minute=0, second=0).format("YYYY-MM-DDTHH:mm:ssZZ")
        time_max = tnow.replace(hour=20, minute=0, second=0).format("YYYY-MM-DDTHH:mm:ssZZ")
        self._url = self._base_calendar_url + f"&timeMin={time_min}&timeMax={time_max}"
        resp = self.fetch(self._url,'Fetching Calendar',tnow.format('MM/DD/YYYY hh:mm A ZZZ'))
        if resp is not None:
            items = resp['items']
            data = {
                'type': self.type,
                'updated': tnow.format('MM/DD/YYYY h:mm A ZZZ'),
                'valid': tnow.shift(seconds=self.update_period).format('MM/DD/YYYY h:mm:ss A ZZZ'),
                'values': [(item["summary"], item["start"]["dateTime"], item["end"]["dateTime"]) for item in items]
            }

            # print(json.dumps(data,indent=2))
            self.dba.write(data)
            print(f'{type(self).__name__} updated.')

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
        CalendarServer(True, 877).run()
    else:
        CalendarServer(False, 877, SECRETS_PATH).run()
