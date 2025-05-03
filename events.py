""" reads events.json and loads it into the database """
import json
import arrow
from plain_pages.serverpage import ServerPage

class NextEvent(ServerPage):
    """ ... """
    def __init__(self, prod, period):
        super().__init__(prod, period)
        self.type = 'Events'

    def update(self):
        tnow = arrow.now().to('US/Eastern')
        with open('events.json', 'r') as f:
            values = json.load(f)

        data = {
            'type'   : 'Events',
            'updated': tnow.format('MM/DD/YYYY h:mm A ZZZ'),
            'valid'  : tnow.shift(seconds=+self.update_period).format('MM/DD/YYYY h:mm:ss A ZZZ'),
            'values' : values
        }

        print(f'{type(self).__name__} updated.')
        self.dba.write(data)

if __name__ == '__main__':
    import os
    import dotenv

    try:
        PROD = os.environ["PROD"]
    except KeyError:
        pass

    if PROD == '1':
        NextEvent(True, 3593).run()
    else:
        dotenv.load_dotenv()
        NextEvent(False, 3593).run()
