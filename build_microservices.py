import subprocess
import time

import arrow
import json
import requests
from requests.exceptions import HTTPError

from securedict    import DecryptDicts      # decrypt the secretsecrets
from secretsecrets import encsecrets        # encrypted configuration values

ALL = ['aqi', 'calendar', 'garmin', 'github', 'jenkins', 'mlb', 'moon', 'events', 'weather']

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

def build_one(tag):
    build_image(tag)
    time.sleep(1)
    push_image(tag)
    time.sleep(1)
    deploy_image(tag)

def build_all():
    print('Building all:')
    for i in ALL:
        build_one(i)
        time.sleep(1)

def build_aqi():
    build_one('aqi')

def build_calendar():
    build_one('calendar')

def build_garmin():
    build_one('garmin')

def build_github():
    build_one('github')

def build_jenkins():
    build_one('jenkins')

def build_mlb():
    build_one('mlb')

def build_moon():
    build_one('moon')

def build_events():
    build_one('events')

def build_weather():
    build_one('weather')

def build_none():
    print('No images to build')

# to-do: collapse these two dicts into one
reverse_dependencies = {
    "build_microservices.py": "None",
    "aqiserver.py": "AQI",
    "aqi_data.py": "AQI",
    "Dockerfile.aqi": "AQI",
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
    "AQI": build_aqi,
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
            if reverse_dependencies[f] == 'ALL':
                build_list = ['ALL']
                break
            else:
                build_list.append(reverse_dependencies[f])
        except KeyError:
            pass
        # print(f)
    #
    #build_list = ['ALL']
    #    
    print(f'Images to build: {list(set(build_list))}')

    # actually build the image(s)
    for b in build_list:
        builds[b]()
   
    if file_list != []:
        last_sha = commits[0]["sha"]
        print(f'new last_sha = {last_sha}')
        with open('last_sha.txt', 'wt', encoding='utf-8') as file:
            file.write(f'{last_sha}')
            file.close()
