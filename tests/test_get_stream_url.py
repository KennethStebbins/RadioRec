from app.get_stream_url import get_stream_url
import re, unittest

class TestGetOneStreamUrl(unittest.TestCase):
    def test_get_one_stream_url(self):
        result = get_stream_url()

        # https://14543.live.streamtheworld.com/KMGLFMAAC.aac
        self.assertRegex(result, r'^https?://\d+\.live\.streamtheworld\.com/KMGLFMAAC\.aac')

class TestGetMultipleStreamUrls(unittest.TestCase):
    def test_get_multiple_stream_urls(self):
        firstOne = get_stream_url()
        secondOne = get_stream_url()

        # firstSubdomainName = re.match(
        #     r'https?://(\d+)\.live\.streamtheworld\.com/', firstOne).group(1)
        # firstSubdomainName = int(firstSubdomainName)

        # secondSubdomainName = re.match(
        #     r'https?://(\d+)\.live\.streamtheworld\.com/', firstOne).group(1)
        # secondSubdomainName = int(secondSubdomainName)

        # self.assertNotEqual(firstSubdomainName, secondSubdomainName)

        self.assertNotEqual(firstOne, secondOne)

if __name__ == '__main__':
    unittest.main()