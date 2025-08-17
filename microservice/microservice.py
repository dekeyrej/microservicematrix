""" ... """
import json
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import os
import time


import arrow
import socketserver                         # for liveness probe (MyTCPHandler(), TCPServer)
import requests   
from   requests.exceptions import HTTPError #, ConnectionError
from   requests.adapters   import HTTPAdapter, Retry
from   redis               import Redis

from   secretmanager       import SecretManager      # for reading secrets from Vault, K8s, or environment variables

class MicroService:
    """ ... """
    def __init__(self, period: int, secretcfg: dict, secretdef: dict, log_level: str = 'INFO'):
        self.type = None
        self.rsess = requests.session()
        retries = Retry(total=5,
                        backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504])
        self.rsess.mount('https://', HTTPAdapter(max_retries=retries))
        self.secrets = self.read_secrets(secretcfg, secretdef)
        self.timezone = self.secrets.get('timezone', 'America/New_York')
        self.health_port = self.secrets.get('health_port', '0')
        redis_url = self.secrets.get('redis_url', 'redis://redis.redis:6379/0')
        self.r = self.connect_redis(redis_url)
        self.update_period = period
        self.last_update = 0
        self.output = False

    def read_secrets(self, secretcfg: dict, secretdef: dict):
        """ Read secrets from a file, Vault, Kubernetes, or environment variables. """
        sm = SecretManager(secretcfg, log_level='INFO')
        try:
            read_result = sm.execute(secretcfg.get("SOURCE"), "READ", sm, secretdef)
            if read_result.get("status") == "success":
                logger.info("Secrets retrieved successfully.")
            else:
                logger.error(f"Failed to retrieve secrets: {read_result.get('error', 'Unknown error')}")
            # logger.info(f"Secrets:\n{json.dumps(read_result.get('data', {}), indent=4)}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
        result = sm.execute(secretcfg.get("SOURCE"), "LOGOUT", sm)
        del sm  # Clean up the SecretManager instance
        return read_result.get('data', {})

    def connect_redis(self, redis_url: str):
        r = Redis.from_url(redis_url, decode_responses=True)
        if not r.ping():
            raise ConnectionError(f"Could not connect to Redis at {redis_url}")
        logging.info(f"Connected to Redis at {redis_url}")
        return r
    
    def update(self): # really must be overridden...
        """ ... """
        logging.info(f"{type(self).__name__} updated.")

    def check(self, now: float):
        """ ... """
        if self.last_update == 0 or now - self.last_update > self.update_period:
            self.last_update = now
            logging.info(f'Updating {type(self).__name__}...')
            self.update()
            logging.info(f"{arrow.now().to(self.timezone).format('MM/DD/YYYY h:mm:ss A ZZZ')}: " \
                  f"{type(self).__name__} updated.")

    def run(self):
        """ ... """
        # Write Startup record to redis
        tnow = arrow.now()
        data = {}
        data['type']   = f'{self.type}-Server'
        data['updated'] = tnow.to(self.timezone).format('MM/DD/YYYY h:mm A Z')
        data['valid']   = tnow.to(self.timezone).format('MM/DD/YYYY h:mm:ss A Z')
        data['values'] = {'message': f'{type(self).__name__} started.'}
        self.r.publish('update', json.dumps(data))

        if self.health_port != "0":
            HOST = '0.0.0.0'
            PORT = int(self.health_port)

            class MyTCPHandler(socketserver.BaseRequestHandler):
                # Socket handler for liveness probe
                def handle(self):
                    self.data = self.request.recv(1024).strip()
                    logging.info('Health Check...')
                    self.request.sendall(self.data.upper())

            with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
                server.timeout = 0.1
                while True:
                    now = time.monotonic()
                    self.check(now)
                    server.handle_request()
                    time.sleep(0.9)
        else:
            while True:
                    now = time.monotonic()
                    self.check(now)
                    # server.handle_request()
                    time.sleep(0.95)


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
                logging.error(f'({name}) HTTP error occurred: {http_err} @ {now}')
                return None
            except ConnectionError as http_err:
                logging.error(f'({name}) HTTP error occurred: {http_err} @ {now}')
                return None
            # except Exception as err:
            #     logging.error(f'({name}) Other error occurred: {err} @ {now}')
            #     return None
            else:
                try:
                    logging.debug(response)
                    logging.debug(f'apparent_encoding: [{response.apparent_encoding}]')
                    logging.debug(f'content: [{response.content}]')
                    logging.debug(f'   text: [{response.text}]')
                    values = response.json()
                except json.decoder.JSONDecodeError:
                    raise
                else:
                    return values # response.json()

    def fetch_raw(self, url: str, name: str, now: str):
        """ required for Garmin server which provides an XML response instead of a JSON one """
        with self.rsess as sess:
            try:
                response = sess.get(url,timeout=(5,15))
                response.raise_for_status()
            except HTTPError as http_err:
                logging.error(f'({name}) HTTP error occurred: {http_err} @ {now}')
                return None
            except ConnectionError as http_err:
                logging.error(f'({name}) HTTP error occurred: {http_err} @ {now}')
                return None
            # except Exception as err:
            #     logging.error(f'({name}) Other error occurred: {err} @ {now}')
            #     return None
            return response

    def now_str(self, now: arrow, secs: bool):
        """ ... """
        if secs:
            return now.format('MM/DD/YYYY h:mm:ss A Z')

        return now.format('MM/DD/YYYY h:mm A Z')
    
