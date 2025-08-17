""" reads events.json and loads it into the database """
import json
import arrow
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from microservice import MicroService

class NextEvent(MicroService):
    """ ... """
    def __init__(self, period, secretcfg, secretdef):
        super().__init__(period, secretcfg, secretdef)
        del self.secrets
        self.type = 'Events'

    def update(self):
        tnow = arrow.now().to(self.timezone)
        with open('events.json', 'r') as f:
            values = json.load(f)

        data = {
            'type'   : 'Events',
            'updated': self.now_str(tnow, False),
            'valid'  : self.now_str(tnow.shift(seconds=self.update_period), True),
            'values' : values
        }

        logging.info(f'{type(self).__name__} updated.')
        self.r.publish('update', json.dumps(data))

### test change ###

if __name__ == '__main__':
    import os
    
    period = int(os.environ.get("PERIOD", '600'))

    with open("secretcfg.json") as f:
        secretcfg = json.load(f)

    with open("secretdef.json") as f:
        secretdef = json.load(f)

    logging.debug(f"Starting Events Server with period: {period},\nsecrets type: {secretcfg}, and\nsecret definition: {secretdef}")

    NextEvent(period, secretcfg, secretdef).run()
