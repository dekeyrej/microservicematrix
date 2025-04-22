#!/usr/bin/env bash
export PATH=$HOME/.local/bin:$PATH
# cp ~/agent/workspace/refKey.txt Do_Not_Copy/refKey.txt
# cp ~/agent/workspace/secrets.json .
# cp ~/agent/workspace/events.txt .
python3 -m venv .
source bin/activate
pip install pylint pylint-venv pytest
pip install -r requirements.txt
pylint --fail-under 9.0 *.py
# pytest --verbose --junit-xml ../test-reports/results.xml test_decrypt.py
# rm Do_Not_Copy/refKey.txt
python3 -m compileall *.py
