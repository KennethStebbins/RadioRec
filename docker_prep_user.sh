#!/bin/bash

python -m venv ~/.pyvenv
source ~/.pyvenv/bin/activate

# Upgrade pip and install app's Python dependencies
python -m pip install --upgrade pip
pip install requests selenium