# import json
import arrow

from serverpage import ServerPage

class GithubServer(ServerPage):
    """ Subclass of serverpage for reading Jenkins Build Status events """
    def __init__(self, config, period):
        super().__init__(config, period)
        owner = self.secrets['github_owner']
        repo = self.secrets['github_repo']
        my_token = self.secrets['github_api_key']
        self.url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        self.headers = {'Authorization': f'token {my_token}', 'Accept': 'application/vnd.github+json'}

    def update(self):
        """ called by ServerPage.check() """
        tnow = arrow.now().to('US/Eastern')
        resp = self.fetch(self.url,'Fetching GitHub Commits',\
                          tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                          headers=self.headers)
        # print(json.dumps(resp,indent=2))
        # git diff-tree --no-commit-id --name-only -r {resp[0]['sha'][0:7]}
        if resp is not None:
            data = {}
            data['type']   = 'GitHub'
            data['updated'] = tnow.to('US/Eastern').format('MM/DD/YYYY h:mm A ZZZ')
            data['valid'] = tnow.to('US/Eastern').shift(seconds=+self.update_period).\
                format('MM/DD/YYYY h:mm:ss A ZZZ')
            data['values'] = {}
            data['values']['commit'] = resp[0]['sha'][0:7]
            data['values']['message'] = resp[0]['commit']['message']
            data['values']['date']   = arrow.get(resp[0]['commit']['author']['date'],'YYYY-MM-DD[T]HH:mm:ssZ').to('US/Eastern').format('YYYY-MM-DD hh:mm:ss A ZZZ')

            # print(json.dumps(data,indent=2))
            self.dba.write(data)
            print(f'{type(self).__name__} updated.')
