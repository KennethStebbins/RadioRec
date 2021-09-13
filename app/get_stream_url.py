from selenium.webdriver import Firefox
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.firefox.options import Options

from logging import getLogger

log = getLogger('radiorec')

def get_stream_url(page_url : str = 'https://player.listenlive.co/34461') -> str:
    """
    Loads a player.listenlive.co webpage and extracts a raw streaming URL from it

    NOTE: This process is _slooooow_. It may take 5 or 10 seconds to complete, since
    it's literally opening up a browser, navigating to the webpage, and starting the
    stream just to see the URLs the page accesses. You'll likely want to run this
    asychronously.
    """

    log.debug('get_stream_url called')

    def stream_has_started(driver):
        ecAdBreakTextPresent = expected_conditions.text_to_be_present_in_element(adBreakTextSelector, 'In a commercial break...')
        ecNowPlayingCardVisible = expected_conditions.visibility_of_element_located(nowPlayingCardSelector)

        adBreakTextPresent = ecAdBreakTextPresent(driver)
        nowPlayingCardVisible = ecNowPlayingCardVisible(driver)

        return adBreakTextPresent or nowPlayingCardVisible

    def extract_streaming_url(driver):
        js = """
        let regex = /https?:\/\/\d+\.live\.streamtheworld\.com\/[^/]*\.aac/;
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

    nowPlayingCardSelector = (By.ID, 'nowPlayingDisplay')
    adBreakTextSelector = (By.ID, 'td_nowplaying_bigbox_wrapper')
    btnPlaySelector = (By.ID, 'playButton')
    btnStopSelector = (By.ID, 'stopButton')
    btnVolumeSelector = (By.ID, 'volumeButton')

    try:
        opts = Options()
        opts.set_headless()
        browser = Firefox(options=opts)
    except:
        log.exception("Failed to initialize webdriver")
        raise RuntimeError('Failed to initialize webdriver')

    try:
        # Load the page
        browser.get(page_url)

        # Get all of our buttons
        btnPlay = WebDriverWait(browser, 10).until(
            expected_conditions.presence_of_element_located(btnPlaySelector)
        )

        btnStop = WebDriverWait(browser, 10).until(
            expected_conditions.presence_of_element_located(btnStopSelector)
        )
        
        btnVolume = WebDriverWait(browser, 10).until(
            expected_conditions.presence_of_element_located(btnVolumeSelector)
        )

        # Wait until we can click the volume button, then click it to mute the stream
        WebDriverWait(browser, 10).until(
            expected_conditions.element_to_be_clickable(btnVolumeSelector)
        )
        btnVolume.click()

        # Make sure the play button is clickable, then click it
        WebDriverWait(browser, 10).until(
            expected_conditions.element_to_be_clickable(btnPlaySelector)
        )
        btnPlay.click()

        # Wait until it looks like the stream has started, then click the stop button
        WebDriverWait(browser, 60).until(
            stream_has_started
        )
        btnStop.click()

        # Wait until the streaming URL appears in the browser's performance metrics
        WebDriverWait(browser, 10).until(
            lambda driver : extract_streaming_url(driver) != ''
        )

        # Grab the raw streaming url
        result = extract_streaming_url(browser)

        log.debug(f"Found streaming URL: {result}")

        return result
    except TimeoutException as e:
        log.exception("An expected condition did not become true within the allotted timeout period.")
        raise RuntimeError("Failed to extract streaming URL")
    except:
        log.exception("An unexpected exception occurred while extracting the streaming URL")
        raise RuntimeError("Failed to extract streaming URL")
    finally:
        browser.close()
