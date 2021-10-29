# RadioRec
Only tested on Ubuntu

## Dependencies
### Python modules
- Python 3.9
- Selenium 4.0.0
- Python Requests 2.26.0

### Other requirements
- Mozilla geckodriver v0.30
- Mozilla FireFox 93.0

### Install Dependencies
```bash
## Install geckodriver locally
curl -L 'https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz' | tar -xz
mv geckodriver ~/.local/bin

## Install Firefox locally
curl -L 'https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US' | tar -xj
mv firefox/ ~/.local/lib/
ln -s ~/.local/lib/firefox/firefox ~/.local/bin

## Install the other dependencies
sudo apt install python3 python3-pip -y
sudo pip3 install selenium requests
```

