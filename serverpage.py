""" ... """
import time
import arrow
from requests.exceptions import HTTPError #, ConnectionError

class ServerPage:
    """ ... """
    def __init__(self, config, period):
        # self.lock = lock
        # self.syslog = syslog
        # self.col = col
        self.dba = config['dba']
        self.rsess = config['sess']
        self.secrets = config['secrets']
        self.update_period = period
        self.last_update = 0

    def update(self): # really must be overridden...
        """ ... """
        print(f"{type(self).__name__} updated.")

    def check(self,now):
        """ ... """
        if self.last_update == 0 or now - self.last_update > self.update_period:
            self.last_update = now
            print(f'Updating {type(self).__name__}...')
            self.update()
            print(f"{arrow.now().to('US/Eastern').format('MM/DD/YYYY h:mm:ss A ZZZ')}: " \
                  f"{type(self).__name__} updated.")

    def run(self):
        """ ... """
        while True:
            now = time.monotonic()
            self.check(now)
            time.sleep(1.0)

    def fetch(self, url, name, now, auth=None, headers=None):
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

    def fetch_raw(self, url, name, now):
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
