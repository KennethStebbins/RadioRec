#!/bin/bash

cd ~

apt update
apt install curl tar bzip2 libgtk-3-0 libx11-xcb1 libdbus-glib-1-2 -y

# Install the gecko driver
curl -sL 'https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz' | tar -xz
mkdir -p /usr/local/lib/geckodriver
mv geckodriver /usr/local/lib/geckodriver
ln -s /usr/local/lib/geckodriver/geckodriver /usr/local/bin

# Install firefox
curl -sL 'https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US' | tar -xj
mv firefox /usr/local/lib
ln -s /usr/local/lib/firefox/firefox /usr/local/bin

adduser --disabled-password --gecos "" radiorec

mkdir -p /output
chown radiorec:radiorec /output

echo "Done!"