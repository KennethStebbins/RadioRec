from requests.api import head
from selenium.webdriver import Firefox
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile

from logging import getLogger

log = getLogger('RadioRec')

def get_stream_url(page_url : str, headless : bool = True) -> str:
    """
    Loads a player.listenlive.co webpage and extracts a raw streaming URL from it

    NOTE: This process is _slooooow_. It may take 5 or 10 seconds to complete, since
    it's literally opening up a browser, navigating to the webpage, and starting the
    stream just to see the URLs the page accesses. You'll likely want to run this
    asychronously.
    """

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

    try:
        opts = Options()
        opts.headless = headless
        opts.set_preference('media.volume_scale', '0.0')
        browser = Firefox(options=opts)
    except:
        log.exception("Failed to initialize webdriver")
        raise RuntimeError('Failed to initialize webdriver')

    try:
        # Load the page
        browser.get(page_url)

        # Get all of our buttons
        btnPlay : WebElement = WebDriverWait(browser, 10).until(
            expected_conditions.presence_of_element_located(btnPlaySelector)
        )

        btnStop : WebElement = WebDriverWait(browser, 10).until(
            expected_conditions.presence_of_element_located(btnStopSelector)
        )

        # Make sure the play button is clickable, then click it
        WebDriverWait(browser, 10).until(
            expected_conditions.element_to_be_clickable(btnPlaySelector)
        )
        btnPlay.click()

        # Wait to progress. If we find a streaming URL, continue. Otherwise,
        # wait for the stream to start. When the stream starts, hit the stop
        # button.
        WebDriverWait(browser, 30).until(
            lambda driver : stream_has_started(driver) or
                                extract_streaming_url(driver) != ''
        )
        if stream_has_started(browser):
            btnStop.click()

        # Wait until the streaming URL appears in the browser's performance metrics
        WebDriverWait(browser, 5).until(
            lambda driver : extract_streaming_url(driver) != ''
        )

        # Grab the raw streaming url
        result = extract_streaming_url(browser)

        return result
    except TimeoutException as e:
        log.exception("An expected condition did not become true within the allotted timeout period.")
        raise e
    except:
        log.exception("An unexpected exception occurred while extracting the streaming URL")
        raise RuntimeError("Failed to extract streaming URL")
    finally:
        browser.close()
