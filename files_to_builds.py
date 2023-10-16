""" 
Build-time utility do determine which microservice images need to be built/redeplloyed
based on which files have been modified since the last successful jenkins build
"""
import os
import build_data
ALL = build_data.services
reverse_dependencies = build_data.reverse_dependencies

with open('modified_files.txt', 'rt') as file:
    files = file.read()
    file.close()
print(files)
# files.replace('ÿþ','')
# file_list = files.replace('ÿþ','').decode().splitlines()
file_list = files.splitlines()
print(file_list)
# file_list = list(set(out_files))[1:]
# print(f'Unique files changed since {last_sha}: {str(file_list)}')

build_list = []
for f in file_list:
    try:
        if reverse_dependencies[f] == 'all':
            print('Build all!')
            build_list = ALL
            break
        build_list.append(reverse_dependencies[f])
    except KeyError:
        pass

bl = list(set(build_list))
bl.sort()
print(bl)
with open('builds.txt', 'wt', encoding='utf-8') as file:
    for b in bl:
        # print(f'{b}')
        file.write(f'{b}\n')
    file.close()
