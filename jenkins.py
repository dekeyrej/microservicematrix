''' Checks latest build status for Jenkins project '''

# import json
import arrow

from serverpage import ServerPage

class JenkinsServer(ServerPage):
    """ Subclass of serverpage for reading Jenkins Build Status events """
    def __init__(self, config, period):
        super().__init__(config, period)
        self.server = "rocket3"
        self.port = 8080
        self.project = "CRServer"
        self._server_url = f"http://{self.server}:{self.port}/job/{self.project}/api/json"
        self._build_stem_url = f"http://{self.server}:{self.port}/job/{self.project}"


    def update(self):
        """ called by ServerPage.check() """
        tnow = arrow.now().to('US/Eastern')
        sresp = self.fetch(self._server_url,'Fetching Jenkins CRServer',\
                           tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                           auth=(self.secrets['jenkins_user'],self.secrets['jenkins_api_key']))
        # health = sresp['healthReport'][0]['score']
        # print(json.dumps(sresp,indent=2))
        build_url = f'{self._build_stem_url}/{sresp["builds"][0]["number"]}/api/json'
        resp = self.fetch(build_url,'Fetching CRServer Build',\
                          tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                          auth=(self.secrets['jenkins_user'],self.secrets['jenkins_api_key']))
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
