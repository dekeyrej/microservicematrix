''' Looks for latest commit to github repository '''
import json
import arrow

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from microservice import MicroService

class GithubServer(MicroService):
    """ Subclass of serverpage for reading Jenkins Build Status events """
    def __init__(self, period, secretcfg, secretdef):
        super().__init__(period, secretcfg, secretdef)

        self.type = 'GitHub'
        owner = self.secrets['github_owner']
        repo = self.secrets['github_repo']
        workflow_id = 'build_apps.yaml'
        my_token = self.secrets['github_api_key']
        del self.secrets
        self.curl = f'https://api.github.com/repos/{owner}/{repo}/commits'
        self.lscurl = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs'
        self.headers = {'Authorization': f'token {my_token}',
                        'Accept': 'application/vnd.github+json'}

    def update(self):
        """ called by ServerPage.check() """
        in_format = 'YYYY-MM-DD[T]HH:mm:ssZ'
        out_format = 'YYYY-MM-DD hh:mm:ss A ZZZ'
        tnow = arrow.now().to(self.timezone)
        cresp = self.fetch(self.curl,'Fetching GitHub Commits',\
                          tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                          headers=self.headers)
        lscresp = self.fetch(self.lscurl,'Fetching GitHub Workflow Runs',\
                          tnow.format('MM/DD/YYYY hh:mm A ZZZ'),\
                          headers=self.headers)
        if cresp and lscresp:
            data = {
                'type': self.type,
                'updated': self.now_str(tnow, False),
                'valid': self.now_str(tnow.shift(seconds=self.update_period), True),
                'values': {
                    'latest_commit': cresp[0]['sha'][0:7],
                    'last_successful_commit': self.find_last_successful_commit(lscresp),
                    'commit_message': cresp[0]['commit']['message'],
                    'date': arrow.get(cresp[0]['commit']['author']['date'], in_format).to(self.timezone).format(out_format)
                }
            }
            # data['values']['date'] = commit_date.to(self.timezone).format(out_format)

            logging.info(json.dumps(data,indent=2))
            self.r.publish('update', json.dumps(data))
            logging.info(f'{type(self).__name__} updated.')

    def find_last_successful_commit(self, resp):
        for r in resp['workflow_runs']:
            if r['conclusion'] == 'success':
                return r['head_commit']['id'][0:7]
        return '0000000'

if __name__ == '__main__':
    import os

    period = int(os.environ.get("PERIOD", '600'))

    with open("secretcfg.json") as f:
        secretcfg = json.load(f)

    with open("secretdef.json") as f:
        secretdef = json.load(f)

    logging.debug(f"Starting GitHub Server with period: {period},\nsecrets type: {secretcfg}, and\nsecret definition: {secretdef}")

    GithubServer(period, secretcfg, secretdef).run()
