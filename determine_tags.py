import os
import subprocess
import json

import arrow
import requests
from requests.exceptions import HTTPError

import dotenv
dotenv.load_dotenv()

import kube
ks = kube.kube_secrets(False)
secrets = ks.read_secret("default", "matrix-secrets", "secrets.json", True) # for test and prod

import build_data
ALL = build_data.services
reverse_dependencies = build_data.reverse_dependencies

sess = requests.session()

def fetch(rsess, url, name, auth=None, headers=None):
    """ ... """
    # name = "GitHub"
    now = arrow.now().format('MM/DD/YYYY hh:mm A ZZZ')
    with rsess as sess:
        try:
            if auth is None and headers is None:
                response = sess.get(url,timeout=(5,15))
            elif headers is None:
                response = sess.get(url,timeout=(5,15),auth=auth)
            else:
                response = sess.get(url,timeout=(5,15),headers=headers)
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'({name}) HTTP error occurred: {http_err} @ {now}')
            return None
        except ConnectionError as http_err:
            print(f'({name}) HTTP error occurred: {http_err} @ {now}')
            return None
        # except Exception as err:
        #     print(f'({name}) Other error occurred: {err} @ {now}')
        #     return None
        return response.json()

# get the SHA1 of the last successful build from Jenkins
if os.environ['PROD'] == '0':
    jserver  = "rocket2"
    jport    = 32005
else:
    jserver  = secrets['jenkins_host']
    jport    = secrets['jenkins_port']
jproject = secrets['jenkins_project']
jserver_url = f"http://{jserver}:{jport}/job/{jproject}/lastSuccessfulBuild/api/json"
jauth       = (secrets['jenkins_user'],secrets['jenkins_api_key'])
# print(f'URL: {jserver_url}, with auth {jauth}')
jresp = fetch(sess, jserver_url, 'Jenkins', auth=jauth)
last_sha = jresp['changeSets'][0]['items'][0]['commitId'][0:7]
print(f'Commit for lastest successful build: {last_sha}')

# get the list of commits from GitHub
owner    = secrets['github_owner']
repo     = secrets['github_repo']
my_token = secrets['github_api_key']
url = f'https://api.github.com/repos/{owner}/{repo}/commits'
headers = {'Authorization': f'token {my_token}', 
           'Accept': 'application/vnd.github+json'}
resp = fetch(sess, url, 'GitHub', headers=headers)

in_format = 'YYYY-MM-DD[T]HH:mm:ssZ'
out_format = 'YYYY-MM-DD hh:mm:ss A ZZZ'

if resp is not None:
    resp_count = len(resp)
    commits = []
    out_files = []
#     newest_sha = resp[0]['sha'][0:7]
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
            else:
                build_list.append(reverse_dependencies[f])
        except KeyError:
            pass
        
    bl = list(set(build_list))
    print(bl)
    with open('builds.txt', 'wt', encoding='utf-8') as file:
        for b in bl:
            print(f'{b}')
            file.write(f'{b}\n')
        file.close
