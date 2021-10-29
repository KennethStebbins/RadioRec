#!/bin/bash

cd ~

sudo apt update
sudo apt install python3 python3-pip -y

# Upgrade pip and install app's Python dependencies
python3 -m pip install --upgrade pip
pip3 install requests selenium

sudo mkdir /usr/local/radiorec/output
sudo chown -R seluser:seluser /usr/local/radiorec/output

echo "Done!"