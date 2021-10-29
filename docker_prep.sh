#!/bin/bash

cd ~

#apk add curl tar
apt update -y
apt install curl tar bzip2 -y

#curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Install dependencies for python cryptography library
#apk add gcc musl-dev python3-dev libffi-dev openssl-dev cargo

# Upgrade pip and install app's Python dependencies
python -m pip install --upgrade pip
pip install requests selenium

# Install the gecko driver
curl -sL 'https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz' | tar -xz
mkdir -p /usr/local/lib/geckodriver
mv geckodriver /usr/local/lib/geckodriver
ln -s /usr/local/lib/geckodriver/geckodriver /usr/local/bin

# Install firefox
curl -sL 'https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US' | tar -xj
mv firefox /usr/local/lib
ln -s /usr/local/lib/firefox/firefox /usr/local/bin

# Remove build dependencies
#apk del gcc musl-dev python3-dev libffi-dev openssl-dev cargo
#~/.cargo/bin/rustup self uninstall -y

echo "Done!"