import json
import subprocess

import requests

import build_data

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

    def update_github(self):
        latest_sha, last_commit = self.get_latest_commit()
        last_successful_sha, last_success = self.get_last_successful_commit()
        print(f'Latest commit: {latest_sha} @ {last_commit}. Last successful commit: {last_successful_sha} @ {last_success}')
        return last_successful_sha, latest_sha

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

    def get_modified_files(self, successful_sha, latest_sha):
        cmd = f'git diff-tree {successful_sha} {latest_sha} --no-commit-id --name-only'
        result = subprocess.run(cmd, shell=True, capture_output=True)
        # print(f'return code: {result.returncode}')
        if result.returncode == 0:
            files = result.stdout.decode('utf-8').split('\n')
            print(f'Files changed since {successful_sha}: {files}')
        else:
            files = []
        return files

    def get_builds(self, files):
        build_list = []
        for f in files:
            try:
                if build_data.reverse_dependencies[f] == 'all':
                    print('Build all!')
                    build_list = build_data.services
                    break
                build_list.append(build_data.reverse_dependencies[f])
            except KeyError:
                pass

        bl = list(set(build_list))
        bl.sort()
        # print(bl)

        builds = {}
        builds['include'] = []
        for a in bl:
            builds['include'].append({"app": a})
        print(json.dumps(builds))
        with open('builds.json', 'wt', encoding='utf-8') as file:
            file.write(json.dumps(builds))
            file.close()

if __name__ == '__main__':
    ll = LandL()
    success, latest = ll.update_github()
    filelist = ll.get_modified_files(success, latest)
    ll.get_builds(filelist)