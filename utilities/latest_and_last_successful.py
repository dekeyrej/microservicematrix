import json
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
import subprocess
import os
import requests

import build_data

class LandL():
    def __init__(self):
        owner = 'dekeyrej'
        repo = 'microservicematrix'
        workflow = 'build_apps.yaml'
        token = os.getenv('GITHUB_TOKEN')  # Use environment variable for the token
        self.commits_url = f'https://api.github.com/repos/{owner}/{repo}/commits'
        self.workflow_url = f'https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/runs'
        self.headers = {'Authorization': f'token {token}',
                        'Accept': 'application/vnd.github+json'}
        self.rsess = requests.session()

    def update_github(self):
        latest_sha, last_commit = self.get_latest_commit()
        last_successful_sha, last_success = self.get_last_successful_commit()
        logging.debug(f'Latest commit: {latest_sha} @ {last_commit}. Last successful commit: {last_successful_sha} @ {last_success}')
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
        # print(resp)
        return resp[0]['sha'], resp[0]['commit']['author']['date']

    def get_last_successful_commit(self):
        resp = self.fetch(self.workflow_url, self.headers)
        for r in resp['workflow_runs']:
            if r['conclusion'] == 'success':
                return r['head_commit']['id'], r['head_commit']['timestamp']
        return '0000000', 'never'

    def get_modified_files(self, successful_sha, latest_sha):
        cmd = f'git diff-tree {successful_sha} {latest_sha} --no-commit-id --name-only'
        result = subprocess.run(cmd, shell=True, capture_output=True)
        logging.debug(f'return code: {result.returncode}')
        if result.returncode == 0:
            files = result.stdout.decode('utf-8').split('\n')
            logging.debug(f'Files changed since {successful_sha}: {files}')
        else:
            logging.debug(result.stdout.decode('utf-8').split('\n'))
            files = []
        return files

    def get_builds(self, files):
        # build_list = ["mycal"]
        build_list = []
        for f in files:
            f = f.strip()
            base = os.path.basename(f)
            try:
                if build_data.reverse_dependencies[base] == 'all':
                    # print('Build all!')
                    build_list = build_data.services
                    break
                build_list.append(build_data.reverse_dependencies[base])
            except KeyError:
                pass

        bl = list(set(build_list))
        bl.sort()
        # with open('builds.txt', 'wt', encoding='utf-8') as file:
        #     for b in bl:
        #         file.write(b + '\n')
        #     file.close()
        logging.debug(bl)

        # builds = {}
        # builds = {'include': [{'app': a} for a in bl]}
        # for a in bl:
        #     builds['include'].append({"app": a})
        # logging.debug(json.dumps(builds))
        return bl
        # with open('builds.json', 'wt', encoding='utf-8') as file:
        #     file.write(json.dumps(builds))
        #     file.close()

if __name__ == '__main__':
    import os

    if os.getenv("DEBUG_FORCE_APPS") == 'true':
        print(json.dumps(build_data.services))
        exit(0)
    ll = LandL()
    success, latest = ll.update_github()
    filelist = ll.get_modified_files(success, latest)
    builds = ll.get_builds(filelist)
    # print(f'Files changed since {success}: {filelist}')

    # Output the builds as a GitHub Actions output variable
    # print(builds)
    print(json.dumps(builds))