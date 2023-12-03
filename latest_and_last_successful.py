import requests


class LandL():
    def __init__(self):
        owner = 'dekeyrej'
        repo = 'microservicematrix'
        workflow = 'build_apps.yaml'
        token = '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'
        self.commits_url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        self.workflow_url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/runs'
        self.headers = {'Authorization': f'token {token}',
                        'Accept': 'application/vnd.github+json'}
        self.rsess = requests.session()

    def update(self):
        latest_sha, last_commit = self.get_latest_commit()
        with open('latest.sha', 'wt') as file:
            file.write(latest_sha)
            file.close()
        last_successful_sha, last_success = self.get_last_successful_commit()
        with open('last_successful.sha', 'wt') as file:
            file.write(last_successful_sha)
            file.close()
        print(f'Latest commit: {latest_sha} @ {last_commit}. Last successful commit: {last_successful_sha} @ {last_success}')

    def fetch(self, url, headers): 
        """ ... """
        with self.rsess as sess:
            try:
                response = sess.get(url,timeout=(5,15),headers=headers)
                response.raise_for_status()
            except Exception as err:
                print(f'Error {err} occurred.')
                return None
            else:
                return response.json()

    def get_latest_commit(self):
        resp = self.fetch(self.commits_url, self.headers)
        return resp[0]['sha'][0:7], resp[0]['commit']['author']['date']

    def get_last_successful_commit(self):
        resp = self.fetch(self.workflow_url, self.headers)
        for r in resp['workflow_runs']:
            if r['conclusion'] == 'success':
                return r['head_commit']['id'][0:7], r['head_commit']['timestamp']
        return '0000000', 'never'

if __name__ == '__main__':
    ll = LandL()
    ll.update()