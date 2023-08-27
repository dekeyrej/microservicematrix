''' Looks for latest commit to github repository '''
# import json
import arrow

from pages.serverpage import ServerPage

class GithubServer(ServerPage):
    """ Subclass of serverpage for reading Jenkins Build Status events """
    def __init__(self, prod, period, path: str=None):
        super().__init__(prod, period, path)
        self.type = 'GitHub'
        owner = self.secrets['github_owner']
        repo = self.secrets['github_repo']
        my_token = self.secrets['github_api_key']
        self.clear_secrets()
        self.url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        self.headers = {'Authorization': f'token {my_token}',
                        'Accept': 'application/vnd.github+json'}

    def update(self):
        """ called by ServerPage.check() """
        in_format = 'YYYY-MM-DD[T]HH:mm:ssZ'
        out_format = 'YYYY-MM-DD hh:mm:ss A ZZZ'
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
            commit_date = arrow.get(resp[0]['commit']['author']['date'],in_format)
            data['values']['date'] = commit_date.to('US/Eastern').format(out_format)

            # print(json.dumps(data,indent=2))
            self.dba.write(data)
            print(f'{type(self).__name__} updated.')

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
        GithubServer(False, 599, SECRETS_PATH).run()
