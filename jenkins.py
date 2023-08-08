''' Checks latest build status for Jenkins project '''

# import json
import arrow

from pages import ServerPage

class JenkinsServer(ServerPage):
    """ Subclass of serverpage for reading Jenkins Build Status events """
    def __init__(self, prod, period):
        super().__init__(prod, period)
        self.type = 'Jenkins'
        self.server = "rocket3"
        self.port = 8080
        self.project = "CRServer"
        self._server_url = f"http://{self.server}:{self.port}/job/{self.project}/api/json"
        self._build_stem_url = f"http://{self.server}:{self.port}/job/{self.project}"
        self.auth = (self.secrets['jenkins_user'],self.secrets['jenkins_api_key'])
        self.clear_secrets()


    def update(self):
        """ called by ServerPage.check() """
        tnow = arrow.now().to('US/Eastern')
        sresp = self.fetch(self._server_url,'Fetching Jenkins CRServer',\
                           tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                           auth=self.auth)
        # health = sresp['healthReport'][0]['score']
        # print(json.dumps(sresp,indent=2))
        build_url = f'{self._build_stem_url}/{sresp["builds"][0]["number"]}/api/json'
        resp = self.fetch(build_url,'Fetching CRServer Build',\
                          tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                          auth=self.auth)
        # print(json.dumps(resp,indent=2))
        if resp is not None:
            data = {}
            data['type']   = 'Jenkins'
            data['updated'] = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
            data['valid'] = tnow.to('US/Eastern').shift(seconds=+self.update_period).\
                format('MM/DD/YYYY h:mm:ss A ZZZ')
            data['values'] = {}
            data['values']['build']  = sresp["builds"][0]["number"]
            data['values']['status'] = resp['result']
            times = arrow.get(resp['timestamp']).to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
            data['values']['time']   = times
            data['values']['health'] = sresp['healthReport'][0]['score']
            data['values']['icon']   = sresp['healthReport'][0]['iconUrl']
            # print(json.dumps(data,indent=2))
            self.dba.write(data)
            print(f'{type(self).__name__} updated.')

if __name__ == '__main__':
    import os
    try:
        PROD = os.environ["PROD"]
    except KeyError:
        pass
    
    if PROD == '1':
        JenkinsServer(True, 881).run()
    else:
        JenkinsServer(False, 881).run()
