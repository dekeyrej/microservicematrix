""" 
Build-time utility do determine which microservice images need to be built/redeplloyed
based on which files have been modified since the last successful jenkins build
"""
import os
import subprocess

import requests
from requests.exceptions import HTTPError

import kube
import build_data

kks = kube.KubeSecrets(True)
secrets = kks.read_secret("default", "matrix-secrets", "secrets.json", True) # for test and prod
ALL = build_data.services
reverse_dependencies = build_data.reverse_dependencies
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
jresp = fetch(sess, jserver_url, 'Jenkins', auth=jauth)
try:
    last_sha = jresp['changeSets'][0]['items'][0]['commitId'][0:7]
except IndexError:
    last_sha = 'cf6d7f0'
print(f'Commit for lastest successful build: {last_sha}')

# get the list of commits from GitHub
owner    = secrets['github_owner']
repo     = secrets['github_repo']
my_token = secrets['github_api_key']
gurl = f'https://api.github.com/repos/{owner}/{repo}/commits'
gheaders = {'Authorization': f'token {my_token}',
           'Accept': 'application/vnd.github+json'}
resp = fetch(sess, gurl, 'GitHub', headers=gheaders)

if resp is not None:
    resp_count = len(resp)
    commits = []
    out_files = []
    print(f"Latest commit: {resp[0]['sha'][0:7]}")
    for i in range(resp_count):
        sha = resp[i]['sha'][0:7]
        cmd = f"git diff-tree --no-commit-id --name-only -r {sha}"
        if sha == last_sha:
            break
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            if result.returncode == 0:
                files = result.stdout.decode('utf-8').split('\n')
                out_files.extend(files)
                print(f'Files changed in {sha}: {files}')
            else:
                files = []

    file_list = list(set(out_files))[1:]
    print(f'Unique files changed since {last_sha}: {str(file_list)}')

    build_list = []
    for f in file_list:
        try:
            if reverse_dependencies[f] == 'all':
                build_list = ALL
                break
            build_list.append(reverse_dependencies[f])
        except KeyError:
            pass

    bl = list(set(build_list))
    print(bl)
    with open('builds.txt', 'wt', encoding='utf-8') as file:
        for b in bl:
            print(f'{b}')
            file.write(f'{b}\n')
        file.close()
