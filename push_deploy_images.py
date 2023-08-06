import subprocess
import time

import arrow
import json
import requests
from requests.exceptions import HTTPError

from securedict    import DecryptDicts      # decrypt the secretsecrets
from secretsecrets import encsecrets        # encrypted configuration values

import build_data

ALL = build_data.services

def push_image(tag):
    print(f'Pushing {tag} to cluster...')
    cmd = f'docker push 192.168.86.49:32000/{tag}:registry'
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode == 0:
        print(f'{tag} pushed successfuly.')
    else:
        print(f'{tag} failed to be pushed.')

def deploy_image(tag):
    print(f'Deploying {tag}')
    cmd = f'kubectl rollout restart -n default deployment {tag}'
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode == 0:
        print(f'{tag} deployed.')
    else:
        print(f'{tag} failed to deploy.')

def push_all():
    for m in ALL:
        push_image(m)

def deploy_all():
    for m in ALL:
        deploy_image(m)
        time.sleep(5.0)

reverse_dependencies = build_data.reverse_dependencies

def fetch(rsess, url, auth=None, headers=None):
    """ ... """
    name = "GitHub"
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

with open('last_sha.txt', 'rt', encoding='utf-8') as file:
            last_sha = file.read()
            file.close()
# print(last_sha)
sess = requests.session()
dd = DecryptDicts()
dd.read_key_from_cluster()
secrets = dd.decrypt_dict(encsecrets)

owner = secrets['github_owner']
repo = 'microservicematrix'
# repo = secrets['github_repo']
my_token = secrets['github_api_key']
url = f'https://api.github.com/repos/{owner}/{repo}/commits'
headers = {'Authorization': f'token {my_token}', 
           'Accept': 'application/vnd.github+json'}

in_format = 'YYYY-MM-DD[T]HH:mm:ssZ'
out_format = 'YYYY-MM-DD hh:mm:ss A ZZZ'

resp = fetch(sess, url, headers=headers)

if resp is not None:
    resp_count = len(resp)
    commits = []
    out_files = []
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
            message = resp[i]['commit']['message']
            commit_date = arrow.get(resp[i]['commit']['author']['date'],in_format)
            commit = {}
            commit['sha']     = sha
            commit['message'] = message
            commit['date']    = commit_date.to('US/Eastern').format(out_format)
            commit['files']   = files
            commits.append(commit)

    # print(json.dumps(commits,indent=2))
    file_list = list(set(out_files))[1:]
    print(f'Unique files changed since {last_sha}: {str(file_list)}')
    
    build_list = []
    for f in file_list:
        try:
            if reverse_dependencies[f] == 'all':
                build_list = ['all']
                break
            else:
                build_list.append(reverse_dependencies[f])
        except KeyError:
            pass
        # print(f)

    print(f'Images to build: {list(set(build_list))}')

    # actually push/deploy the image(s)
    if build_list == ['all']:
        # print('Pushing/Deploying all')
        push_all()
        deploy_all()
    elif build_list != []:
        for b in build_list:
            # print(f'Pushing {b}')
            push_image(b)
        for b in build_list:
            # print(f'Deploying {b}')
            deploy_image(b)
   
    if file_list != []:
        last_sha = commits[0]["sha"]
        print(f'new last_sha = {last_sha}')
        with open('last_sha.txt', 'wt', encoding='utf-8') as file:
            file.write(f'{last_sha}')
            file.close()
