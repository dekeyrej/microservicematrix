import subprocess
import json

import arrow
import requests
from requests.exceptions import HTTPError

# from securedict    import DecryptDicts      # decrypt the secretsecrets
# from secretsecrets import encsecrets        # encrypted configuration values

import build_data

ALL = build_data.services
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

def read_secrets(path):
    with open(path) as file:
        newsecrets = json.loads(file.read())
        file.close()
    return newsecrets

with open('../last_sha.txt', 'rt', encoding='utf-8') as file:
            last_sha = file.read()
            file.close()
# print(last_sha)
sess = requests.session()
# dd = DecryptDicts()
# dd.read_key_from_cluster()
# secrets = dd.decrypt_dict(encsecrets)
secrets = read_secrets('secrets.json')

owner = secrets['github_owner']
# repo = 'microservicematrix'
repo = secrets['github_repo']
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
    newest_sha = resp[0]['sha'][0:7]
    with open('../new_last_sha.txt', 'wt', encoding='utf-8') as file:
        file.write(f'{newest_sha}')
        file.close()
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
                build_list = ALL
                break
            else:
                build_list.append(reverse_dependencies[f])
        except KeyError:
            pass
        
    bl = list(set(build_list))
    with open('builds.txt', 'wt', encoding='utf-8') as file:
        for b in bl:
            print(f'{b}')
            file.write(f'{b}\n')
        file.close
