""" 
    Top-level Dataserver Microservice runner.
    .env => PROD=0 for development
    Dockerfile => ENV PROD=1 for production
    
"""
import os                                   # access local environment (os.environ["key"])
import sys                                  # to politely exit (sys.exit())
import time                                 # time.sleep()
import socketserver                         # for liveness probe (MyTCPHandler(), TCPServer)
import requests                             # to create a shared session and process liveness
import arrow                                # date/time handlling
from dotenv import load_dotenv              # simplify dev/test/prod

from datasourcelib import Database          # wrapper for postgres/cockroach/sqlite/mongodb
from securedict    import DecryptDicts      # decrypt the secretsecrets
from secretsecrets import encsecrets        # encrypted configuration values

from github        import GithubServer
from jenkins       import JenkinsServer
from calserver     import CalendarServer
from nextserver    import NextEvent
from weatherserver import OWMServer
from moonserver    import MoonServer
from mlbserver     import MLBServer
from garmin        import GarminServer

load_dotenv()
# MSSERVERTYPE = 'MLB'
try:
    MSSERVERTYPE = os.environ["MSSERVERTYPE"]
except KeyError:
    print('"MSSERVERTYPE" not found in environment.  Exiting')
    sys.exit()

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
    dd.read_key_from_cluster()
    # REFKEY = os.environ["REFKEY"]
    # dd.set_key(REFKEY)
    # dd.read_key_from_file('Do_Not_Copy/refKey.txt')
    config['secrets'] = dd.decrypt_dict(encsecrets)
    DBHOST = '192.168.86.62'
    DBPORT = 5432
    TBLNAME = 'feed'

db_params = {"user": config['secrets']['dbuser'],
             "pass": config['secrets']['dbpass'], \
             "host": DBHOST, "port":  DBPORT, \
             "db_name": 'matrix', "tbl_name": TBLNAME}

config['dba'] = Database('postgres', db_params)

if MSSERVERTYPE == 'Garmin':
    msserver = GarminServer(config, 601)
elif MSSERVERTYPE == 'Github':
    msserver = GithubServer(config, 599)
elif MSSERVERTYPE == 'Jenkins':
    msserver = JenkinsServer(config, 881)
elif MSSERVERTYPE == 'Calendar':
    msserver = CalendarServer(config, 877)
elif MSSERVERTYPE == 'Events':
    msserver = NextEvent(config, 3593)
elif MSSERVERTYPE == 'Weather':
    msserver = OWMServer(config, 907)
elif MSSERVERTYPE == 'Moon':
    msserver = MoonServer(config, 911)
elif MSSERVERTYPE == 'MLB':
    msserver = MLBServer(config, 29)
else:
    print(f'Undefined server type "{MSSERVERTYPE}".  Exiting')
    sys.exit()

# Write Startup record to database
tnow = arrow.now()
data = {}
data['type']   = f'{MSSERVERTYPE}-Server'
data['updated'] = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
data['valid']   = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm:ss A ZZZ')
data['values'] = {}
config['dba'].write(data)

with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
    server.timeout = 0.1
    while True:
        now = time.monotonic()
        msserver.check(now)
        server.handle_request()
        time.sleep(0.9)
