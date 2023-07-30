""" reads events.txt and loads it into the database """
import json
import arrow

from serverpage import ServerPage

class NextEvent(ServerPage):
    """ subclass of serverpage does NOT use superclass """
    def __init__(self, prod, period):
        super().__init__(prod, period)
        self.type = 'Family'
        self.events_file_name = "events.txt"

    def update(self):
        tnow = arrow.now().to('US/Eastern')

        data = {}
        data['type'] = 'Family'
        data['updated'] = tnow.format('MM/DD/YYYY h:mm A ZZZ')
        data['valid'] = tnow.shift(seconds=+self.update_period).format('MM/DD/YYYY h:mm:ss A ZZZ')

        with open(self.events_file_name, encoding='utf-8') as file:
            data['values'] = json.loads(file.read())
            file.close()

        print(f'{type(self).__name__} updated.')
        self.dba.write(data)

if __name__ == '__main__':
    import os
    try:
        PROD = os.environ["PROD"]
    except KeyError:
        pass
    
    if PROD == '1':
        NextEvent(True, 3593).run()
    else:
        NextEvent(False, 3593).run()
