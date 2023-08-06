import subprocess

import build_data

ALL = build_data.services

def build_image(tag):
    print(f'Building {tag}...')
    cmd = f'docker build -f Dockerfile.{tag} -t 192.168.86.49:32000/{tag}:registry .'
    result = subprocess.run(cmd, shell=True, capture_output=True)
    if result.returncode == 0:
        print(f'{tag} built successfuly.')
    else:
        print(f'{tag} failed to build.')

def build_all():
    print('Building all:')
    for i in ALL:
        build_image(i)
    
build_all()
