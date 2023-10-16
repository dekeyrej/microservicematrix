""" 
Build-time utility do determine which microservice images need to be built/redeplloyed
based on which files have been modified since the last successful jenkins build
"""
import os
import json

import requests
from requests.exceptions import HTTPError

import kube
try:
    runt = int(os.environ['PROD'])
except KeyError:
    print("PROD not found in environment")
    runt = 0

if runt > 0:
    kks = kube.KubeSecrets(True)
else:
    kks = kube.KubeSecrets(False)
secrets = kks.read_secret("default", "matrix-secrets", "secrets.json", True) # for test and prod

sess = requests.session()

def fetch(rsess, url, name, auth=None, headers=None):
    """ ... """
    with rsess as lsess:
        try:
            if auth is None and headers is None:
                response = lsess.get(url,timeout=(5,15))
            elif headers is None:
                response = lsess.get(url,timeout=(5,15),auth=auth)
            else:
                response = lsess.get(url,timeout=(5,15),headers=headers)
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'({name}) HTTP error occurred: {http_err}')
            return None
        except ConnectionError as http_err:
            print(f'({name}) HTTP error occurred: {http_err}')
            return None
        return response.json()

# get the SHA1 of the last successful build from Jenkins
jserver  = secrets['jenkins_host']
jport    = secrets['jenkins_port']
jproject = secrets['jenkins_project']
jserver_url = f"http://{jserver}:{jport}/job/{jproject}/lastSuccessfulBuild/api/json"
jauth       = (secrets['jenkins_user'],secrets['jenkins_api_key'])
# print(f'{jserver_url}:{jauth}')
jresp = fetch(sess, jserver_url, 'Jenkins', auth=jauth)
actions = jresp['actions']
for id, a in enumerate(actions):
    _class = a.get("_class", "not")
    # print(f"{id}: {_class}")
    if _class == 'hudson.plugins.git.util.BuildData':
        last_sha = a['buildsByBranchName']['refs/remotes/origin/main']['marked']['SHA1'][0:7]
        # print(last_sha)

print(f'Commit for last successful build: {last_sha}')
with open('last_successful.sha', 'wt') as file:
    file.write(last_sha)
    file.close()

# get the list of commits from GitHub
owner    = secrets['github_owner']
repo     = secrets['github_repo']
my_token = secrets['github_api_key']
gurl = f'https://api.github.com/repos/{owner}/{repo}/commits'
gheaders = {'Authorization': f'token {my_token}',
           'Accept': 'application/vnd.github+json'}
resp = fetch(sess, gurl, 'GitHub', headers=gheaders)

if resp is not None:
    latest_sha = resp[0]['sha'][0:7]
    # print("latest - success")
    print(f'Latest commit: {latest_sha}')
    with open('latest.sha', 'wt') as file:
        file.write(latest_sha)
        file.close()
else:
    print("latest - failed")