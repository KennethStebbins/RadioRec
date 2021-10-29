#!/bin/bash

cd ~

apt update
apt install python3 -y

# Upgrade pip and install app's Python dependencies
python -m pip install --upgrade pip
pip install requests selenium

echo "Done!"