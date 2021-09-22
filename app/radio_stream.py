import logging
from requests import request
from selenium.common.exceptions import TimeoutException
from urllib3.response import HTTPResponse
from threading import Thread

from app.get_stream_url import get_stream_url
from app.byte_buffer import ByteBuffer

log = logging.getLogger('RadioRec')

class RadioStream(Thread):
    byte_buffer : ByteBuffer = None
    url : str = None

    def __init__(self, buffer_size : int = 307200, attempts : int = 3, *args, **kwargs) -> None:
        self.byte_buffer = ByteBuffer(buffer_size)
        for i in range(0, attempts):
            try:
                self.url = get_stream_url()
                if self.url is not None:
                    break
            except TimeoutException:
                log.debug(f'Failed to get stream URL: Attempt #{i + 1}')

        super().__init__(*args, **kwargs)

    def run(self):
        with request('GET', self.url, stream=True) as r:
            raw : HTTPResponse = r.raw

            while raw.readable():
                self.byte_buffer.append(raw.read(8192))

