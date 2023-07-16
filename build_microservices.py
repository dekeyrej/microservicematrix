import subprocess

import arrow
import json
import requests
from requests.exceptions import HTTPError

from securedict    import DecryptDicts      # decrypt the secretsecrets
from secretsecrets import encsecrets        # encrypted configuration values

ALL = ['calendar', 'garmin', 'github', 'jenkins', 'mlb', 'moon', 'events', 'weather']

def build_image(tag):
    print(f'Building {tag}...')
    cmd = f'docker build -f Dockerfile.{tag} -t 192.168.86.49:32000/{tag}:registry .'
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode == 0:
        print(f'{tag} built successfuly.')
    else:
        print(f'{tag} failed to build.')

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

def build_all():
    print('Building all:')
    for i in ALL:
        build_image(i)
        # push_image(i)
        # deploy_image(i)

def build_calendar():
    build_image('calendar')

def build_garmin():
    build_image('garmin')

def build_github():
    build_image('github')

def build_jenkins():
    build_image('jenkins')

def build_mlb():
    build_image('mlb')

def build_moon():
    build_image('moon')

def build_events():
    build_image('events')

def build_weather():
    build_image('weather')

def build_none():
    print('No images to build')

# to-do: collapse these two dicts into one
reverse_dependencies = {
    "build_microservices.py": "None",
    "calserver.py": "Calendar",
    "Dockerfile.calendar": "Calendar",
    "garmin.py": "Garmin",
    "Dockerfile.garmin": "Garmin",
    "github.py": "GitHub",
    "Dockerfile.github": "GitHub",
    "jenkins.py": "Jenkins",
    "Dockerfile.jenkins": "Jenkins",
    "mlbserver.py": "MLB",
    "Dockerfile.mlb": "MLB",
    "moonserver.py": "Moon",
    "Dockerfile.moon": "Moon",
    "nextserver.py": "Events",
    "Dockerfile.events": "Events",
    "rrjo.py": "ALL",
    "secretsecrets.py": "ALL",
    "serverpage.py": "ALL",
    "weatherserver.py": "Weather",
    "Dockerfile.weather": "Weather",
}

builds = {
    "None": build_none,
    "ALL": build_all,
    "Calendar": build_calendar,
    "Garmin": build_garmin,
    "GitHub": build_github,
    "Jenkins": build_jenkins,
    "MLB": build_mlb,
    "Moon": build_moon,
    "Events": build_events,
    "Weather": build_weather,
}

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

last_sha = "045ede4" # to-do: read this from a file
# last_sha = "62d0db6"
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
            if reverse_dependencies[f] == 'ALL':
                build_list = ['ALL']
                break
            else:
                build_list.append(reverse_dependencies[f])
        except KeyError:
            pass
        # print(f)
    
    print(f'Images to build: {list(set(build_list))}')

    # actually build the image(s)
    for b in build_list:
        builds[b]()
   
    # reset last_sha to commits[0]['sha']
    if file_list != []:
        print(f'new last_sha = {commits[0]["sha"]}')  # to-do: write last_sha out to a file