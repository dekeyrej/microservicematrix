""" reads events.json and loads it into the database """
import json
import arrow
from plain_pages.serverpage import ServerPage

class NextEvent(ServerPage):
    """ ... """
    def __init__(self, prod, period, secretcfg, secretdef):
        super().__init__(prod, period, secretcfg, secretdef)
        del self.secrets
        self.type = 'Events'

    def update(self):
        tnow = arrow.now().to(self.timezone)
        with open('events.json', 'r') as f:
            values = json.load(f)

        data = {
            'type'   : 'Events',
            'updated': tnow.format('MM/DD/YYYY h:mm A Z'),
            'valid'  : tnow.shift(seconds=+self.update_period).format('MM/DD/YYYY h:mm:ss A Z'),
            'values' : values
        }

        print(f'{type(self).__name__} updated.')
        self.dba.write(data)

if __name__ == '__main__':
    import os

    try:
        PROD = os.environ["PROD"]
    except KeyError:
        pass

    if PROD == '1':
        import config as cfg
        secretcfg = cfg.secretcfg
        secretdef = cfg.secretdef
        NextEvent(True, 3593, cfg.secretcfg, cfg.secretdef).run()
    else:
        import devconfig as cfg
        secretcfg = cfg.secretcfg
        secretdef = cfg.secretdef
        NextEvent(False, 3593, cfg.secretcfg, cfg.secretdef).run()

