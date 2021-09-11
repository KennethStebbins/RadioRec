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
wget https://github.com/mozilla/geckodriver/releases/download/v0.29.1/geckodriver-v0.29.1-linux32.tar.gz
tar -xzf geckodriver-v0.29.1-linux32.tar.gz
mv geckodriver ~/.local/bin

## Install the other dependencies
sudo apt install python3 python3-pip python3-pyaudio python3-soundfile -y
sudo pip3 install soundfile numpy selenium
```

