""" ... """
import time
# from typing import Union
import arrow
import socketserver                         # for liveness probe (MyTCPHandler(), TCPServer)
import requests   
from requests.exceptions import HTTPError #, ConnectionError
from requests.adapters   import HTTPAdapter, Retry 

from datasourcelib import Database          # wrapper for postgres/cockroach/sqlite/mongodb
from securedict    import DecryptDicts      # decrypt the secretsecrets
from secretsecrets import encsecrets        # encrypted configuration values

# number = Union[float, int]

class ServerPage:
    """ ... """
    def __init__(self, prod: bool, period: int):
        self.type = None
        self.prod = prod  # boolean: True for Production, False otherwise
        self.rsess = requests.session()
        retries = Retry(total=5,
                        backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504])
        self.rsess.mount('https://', HTTPAdapter(max_retries=retries))
        self.secrets = self.read_secrets()
        self.dba = self.connect_db()
        self.update_period = period
        self.last_update = 0
        
    def read_secrets(self):
        dd = DecryptDicts()
        if self.prod:
            dd.read_in_cluster_key()
        else:
            # dd.read_key_from_cluster()
            # REFKEY = os.environ["REFKEY"]
            # dd.set_key(REFKEY)
            dd.read_key_from_file('Do_Not_Copy/refKey.txt')
        return dd.decrypt_dict(encsecrets)

    def clear_secrets(self):
        self.secrets = None
    
    def connect_db(self):
        DBPORT = 5432
        DBNAME = 'matrix'
        TBLNAME = 'feed'
        
        if self.prod:
            DBHOST = 'mypostgres.default'
        else:
            DBHOST = '192.168.86.62'  #rocket3
        
        db_params = {"user": self.secrets['dbuser'],
             "pass": self.secrets['dbpass'], \
             "host": DBHOST, "port":  DBPORT, \
             "db_name": DBNAME, "tbl_name": TBLNAME}

        return Database('postgres', db_params)

    def update(self): # really must be overridden...
        """ ... """
        print(f"{type(self).__name__} updated.")

    def check(self, now: float):
        """ ... """
        if self.last_update == 0 or now - self.last_update > self.update_period:
            self.last_update = now
            print(f'Updating {type(self).__name__}...')
            self.update()
            print(f"{arrow.now().to('US/Eastern').format('MM/DD/YYYY h:mm:ss A ZZZ')}: " \
                  f"{type(self).__name__} updated.")

    def run(self):
        """ ... """
        # Write Startup record to database
        tnow = arrow.now()
        data = {}
        data['type']   = f'{self.type}-Server'
        data['updated'] = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
        data['valid']   = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm:ss A ZZZ')
        data['values'] = {}
        self.dba.write(data)

        HOST = '0.0.0.0'
        PORT = 10255

        class MyTCPHandler(socketserver.BaseRequestHandler):
            # Socket handler for liveness probe
            def handle(self):
                self.data = self.request.recv(1024).strip()
                print('Health Check...')
                self.request.sendall(self.data.upper())

        with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
            server.timeout = 0.1
            while True:
                now = time.monotonic()
                self.check(now)
                server.handle_request()
                time.sleep(0.9)

    def fetch(self, url: str, name: str, now: str, auth: str=None, headers: str=None): 
        """ ... """
        with self.rsess as sess:
            try:
                if auth is None and headers is None:
                    response = sess.get(url,timeout=(5,15))
                elif headers is None:
                    response = sess.get(url,timeout=(5,15),auth=auth)
                else:
                    response = sess.get(url,timeout=(5,15),headers=headers)
                response.raise_for_status()
            except HTTPError as http_err:
                print(f'({name}) HTTP error occurred: {http_err} @ {now}')
                return None
            except ConnectionError as http_err:
                print(f'({name}) HTTP error occurred: {http_err} @ {now}')
                return None
            # except Exception as err:
            #     print(f'({name}) Other error occurred: {err} @ {now}')
            #     return None
            return response.json()

    def fetch_raw(self, url: str, name: str, now: str):
        """ required for Garmin server which expects an XML response instead of a JSON one """
        with self.rsess as sess:
            try:
                response = sess.get(url,timeout=(5,15))
                response.raise_for_status()
            except HTTPError as http_err:
                print(f'({name}) HTTP error occurred: {http_err} @ {now}')
                return None
            except ConnectionError as http_err:
                print(f'({name}) HTTP error occurred: {http_err} @ {now}')
                return None
            # except Exception as err:
            #     print(f'({name}) Other error occurred: {err} @ {now}')
            #     return None
            return response

    def now_str(self, now: arrow, secs: bool):
        """ ... """
        if secs:
            return now.format('MM/DD/YYYY h:mm:ss A ZZZ')

        return now.format('MM/DD/YYYY h:mm A ZZZ')