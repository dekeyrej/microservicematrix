''' Looks for latest commit to github repository '''
import json
import arrow

from plain_pages.serverpage import ServerPage

class GithubServer(ServerPage):
    """ Subclass of serverpage for reading Jenkins Build Status events """
    def __init__(self, prod, period):
        super().__init__(prod, period)
        self.type = 'GitHub'
        owner = self.secrets['github_owner']
        repo = self.secrets['github_repo']
        workflow_id = 'build_apps.yaml'
        my_token = self.secrets['github_api_key']
        self.curl = f'https://api.github.com/repos/{owner}/{repo}/commits'
        self.lscurl = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs'
        self.headers = {'Authorization': f'token {my_token}',
                        'Accept': 'application/vnd.github+json'}

    def update(self):
        """ called by ServerPage.check() """
        in_format = 'YYYY-MM-DD[T]HH:mm:ssZ'
        out_format = 'YYYY-MM-DD hh:mm:ss A ZZZ'
        tnow = arrow.now().to(self.secrets['timezone'])
        cresp = self.fetch(self.curl,'Fetching GitHub Commits',\
                          tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                          headers=self.headers)
        lscresp = self.fetch(self.lscurl,'Fetching GitHub Workflow Runs',\
                          tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                          headers=self.headers)
        if cresp and lscresp:
            data = {}
            data['type']   = 'GitHub'
            data['updated'] = tnow.to(self.secrets['timezone']).format('MM/DD/YYYY h:mm A ZZZ')
            data['valid'] = tnow.to(self.secrets['timezone']).shift(seconds=+self.update_period).\
                format('MM/DD/YYYY h:mm:ss A ZZZ')
            data['values'] = {}
            data['values']['latest_commit'] = cresp[0]['sha'][0:7]
            data['values']['last_successful_commit'] = self.find_last_successful_commit(lscresp)
            data['values']['commit_message'] = cresp[0]['commit']['message']
            commit_date = arrow.get(cresp[0]['commit']['author']['date'],in_format)
            data['values']['date'] = commit_date.to(self.secrets['timezone']).format(out_format)

            print(json.dumps(data,indent=2))
            self.dba.write(data)
            print(f'{type(self).__name__} updated.')

    def find_last_successful_commit(self, resp):
        for r in resp['workflow_runs']:
            if r['conclusion'] == 'success':
                return r['head_commit']['id'][0:7]
        return '0000000'

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
        GithubServer(True, 599).run()
    else:
        GithubServer(False, 599).run()
