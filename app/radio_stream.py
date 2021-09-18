from requests import request, Response
from selenium.webdriver.common.by import By
from urllib3.response import HTTPResponse
from threading import Thread

from app.get_stream_url import get_stream_url
from app.byte_buffer import ByteBuffer

class RadioStream(Thread):
    byte_buffer : ByteBuffer = None
    url : str = None

    def __init__(self) -> None:
        self.byte_buffer = ByteBuffer()
        self.url = get_stream_url()

    def run(self):
        with request('GET', self.url, stream=True) as r:
            raw : HTTPResponse = r.raw

            while raw.readable():
                self.byte_buffer.append(raw.read(8192))

