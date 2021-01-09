#!/bin/sh
python3 -m venv python3  venv
source ./venv/bin/activate
pip install -r requirements.txt
python keyboard.py
open keylayout_file.htmlkeyboards.html
