# RadioRec

## Dependencies
- Python 3.9
- PyAudio
- PySoundFile
- NumPy
- Mozilla geckodriver
- Selenium

### Install Dependencies
```bash
## Install geckodriver locally
# Check https://github.com/mozilla/geckodriver/releases for the latest geckodriver linux64 release
curl -L 'https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux64.tar.gz' -o geckodriver.tar.gz
tar -xzf geckodriver.tar.gz
mv geckodriver ~/.local/bin
# Clean up
rm geckodriver.tar.gz

## Install Firefox locally
curl -L 'https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US' -o firefox.tar.bz2
tar -xjf firefox.tar.bz2
mv firefox .local/lib/
ln -s ~/.local/lib/firefox/firefox ~/.local/bin
# Clean up
rm firefox.tar.bz2

## Install the other dependencies
sudo apt install python3 python3-pip python3-pyaudio python3-soundfile -y
sudo pip3 install soundfile numpy selenium
```

