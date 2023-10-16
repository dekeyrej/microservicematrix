#!/bin/sh
python last_sha.py
export last_sha=`cat last_successful.sha`
export sha=`cat latest.sha`
git diff-tree $last_sha $sha --no-commit-id --name-only > modified_files.txt
python files_to_builds.py
