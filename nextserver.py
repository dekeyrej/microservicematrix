""" reads events.txt and loads it into the database """
import arrow
from pages.serverpage import ServerPage

class NextEvent(ServerPage):
    """ ... """
    def __init__(self, prod, period, path: str=None):
        super().__init__(prod, period, path)
        self.clear_secrets()
        self.type = 'Family'
        self.events_file_name = "events.txt"

    def update(self):
        tnow = arrow.now().to('US/Eastern')

        data = {}
        data['type'] = 'Family'
        data['updated'] = tnow.format('MM/DD/YYYY h:mm A ZZZ')
        data['valid'] = tnow.shift(seconds=+self.update_period).format('MM/DD/YYYY h:mm:ss A ZZZ')

        if self.prod:
            data['values'] = self.read_kube_secret("default", "matrix-events",
                                                   "events", inkube=True)
        else:
            # data['values'] = self.read_kube_secret("default", "matrix-events",
            #                                      "events", inkube=False)
            data['values'] = self.read_json_from_file(self.events_file_name)

        print(f'{type(self).__name__} updated.')
        self.dba.write(data)

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
        NextEvent(True, 3593).run()
    else:
        NextEvent(False, 3593, SECRETS_PATH).run()
