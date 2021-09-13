from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

nowPlayingCardSelector = (By.ID, 'nowPlayingDisplay')
adBreakTextSelector = (By.ID, 'td_nowplaying_bigbox_wrapper')
def stream_has_started(driver):
    ecAdBreakTextPresent = expected_conditions.text_to_be_present_in_element(adBreakTextSelector, 'In a commercial break...')
    ecNowPlayingCardVisible = expected_conditions.visibility_of_element_located(nowPlayingCardSelector)

    adBreakTextPresent = ecAdBreakTextPresent(driver)
    nowPlayingCardVisible = ecNowPlayingCardVisible(driver)

    return adBreakTextPresent or nowPlayingCardVisible

def extract_streaming_url(driver):
    js = """
    let regex = /KMGLFMAAC\.aac/;
    let performanceEntries = window.performance.getEntries();
    let matchedItem = null;
    for(let i = 0; i < performanceEntries.length; i++) {
        let entry = performanceEntries[i];

        if(entry.name.match(regex)) {
            matchedItem = entry;
            break;
        }
    }

    if(matchedItem === null) {
        return '';
    }

    return matchedItem.name;
    """
    return driver.execute_script(js)



opts = Options()
# opts.set_headless()
profile = FirefoxProfile()
profile.set_preference('media.volume_scale', '0.0')
browser = Firefox(options=opts, firefox_profile=profile)

browser.get('https://player.listenlive.co/34461')

btnPlaySelector = (By.ID, 'playButton')
btnPlay = WebDriverWait(browser, 10).until(
    expected_conditions.presence_of_element_located(btnPlaySelector)
)

btnStopSelector = (By.ID, 'stopButton')
btnStop = WebDriverWait(browser, 10).until(
    expected_conditions.presence_of_element_located(btnStopSelector)
)

# Wait until the page is loaded enough to press play
WebDriverWait(browser, 10).until(
    expected_conditions.element_to_be_clickable(btnPlaySelector)
)

btnPlay.click()

WebDriverWait(browser, 60).until(
    stream_has_started
)

btnStop.click()

WebDriverWait(browser, 10).until(
    lambda driver : extract_streaming_url(driver) != ''
)

result = extract_streaming_url(browser)

print(f"URL is {result}")

browser.close()

print('Done!')