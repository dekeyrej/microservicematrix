""" Reads (google) calendar events for today """
####
import os                                   # access local environment (os.environ["key"])
# import sys                                  # to politely exit (sys.exit())
import time                                 # time.sleep()
import socketserver                         # for liveness probe (MyTCPHandler(), TCPServer)
import requests                             # to create a shared session and process liveness
import arrow                                # date/time handlling

from datasourcelib import Database          # wrapper for postgres/cockroach/sqlite/mongodb
from securedict    import DecryptDicts      # decrypt the secretsecrets
from secretsecrets import encsecrets        # encrypted configuration values
####
# import json
# import arrow

from serverpage import ServerPage

class CalendarServer(ServerPage):
    """ Subclass of serverpage for reading calendar events """
    def __init__(self, config, period):
        super().__init__(config, period)
#       calendar has to be public :-/
        self._base_calendar_url = f'https://www.googleapis.com/calendar/v3/calendars/' \
            f'{self.secrets["google_calendar"]}/events?key={self.secrets["google_api_key"]}' \
            f'&orderBy=starttime&singleEvents=true'
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
            data = {}
            data['type']   = 'Calendar'
            data['updated'] = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
            data['valid'] = tnow.to('US/Eastern').shift(seconds=+self.update_period).\
                format('MM/DD/YYYY h:mm:ss A ZZZ')
            data['values'] = []
            for item in items:
                data['values'].append((item["summary"],item["start"]["dateTime"],\
                                       item["end"]["dateTime"]))
            # print(json.dumps(data,indent=2))
            self.dba.write(data)
            print(f'{type(self).__name__} updated.')


# Run this server
MSSERVERTYPE = 'Calendar'   # UPDATE THIS ONE

try:
    ENVIRONMENT = os.environ["PROD"]
except KeyError:
    ENVIRONMENT = 'NF'

# Values for TCP liveness probe
HOST = '0.0.0.0'
PORT = 10255

class MyTCPHandler(socketserver.BaseRequestHandler):
    """ Socket handler for liveness probe """
    def handle(self):
        self.data = self.request.recv(1024).strip()
        print('Health Check...')
        self.request.sendall(self.data.upper())

config = {}
config['sess'] = requests.session()
dd = DecryptDicts()

print(ENVIRONMENT)
if ENVIRONMENT == '1':  # Production
    print('Running in Production')
    dd.read_in_cluster_key()
    config['secrets'] = dd.decrypt_dict(encsecrets)
    DBHOST = 'mypostgres.default'
    DBPORT = 5432
    TBLNAME = 'feed'
else:  # Development
    print('Running in Development')
    dd.read_key_from_file('Do_Not_Copy/refKey.txt')
    config['secrets'] = dd.decrypt_dict(encsecrets)
    DBHOST = 'rocket2'
    DBPORT = 5432
    TBLNAME = 'feed'

db_params = {"user": config['secrets']['dbuser'],
             "pass": config['secrets']['dbpass'], \
             "host": DBHOST, "port":  DBPORT, \
             "db_name": 'matrix', "tbl_name": TBLNAME}

config['dba'] = Database('postgres', db_params)

# Write Startup record to database
tnow = arrow.now()
data = {}
data['type']   = f'{MSSERVERTYPE}-Server'
data['updated'] = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
data['valid']   = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm:ss A ZZZ')
data['values'] = {}
# print(json.dumps(data,indent=2))
config['dba'].write(data)

msserver = CalendarServer(config, 877)  # UPDATE THIS ONE

with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
    server.timeout = 0.1
    while True:
        now = time.monotonic()
        msserver.check(now)
        server.handle_request()
        time.sleep(0.9)
