import logging
from os import devnull
from requests import request
from selenium.common.exceptions import TimeoutException
from urllib3.response import HTTPResponse
from threading import Event, RLock, Thread
from typing import Callable, Iterable, List

from app.get_stream_url import get_stream_url
from app.byte_buffer import ByteBuffer

log = logging.getLogger('RadioRec')

class RadioStream(Thread):
    _byte_buffer : ByteBuffer = None
    _url : str = None
    _preroll_len : int = 63500
    _http_stream : HTTPResponse = None
    
    @property
    def byte_buffer(self):
        return self._byte_buffer
    
    @property
    def url(self):
        return self._url

    def __init__(self, buffer_size : int = 307200, attempts : int = 3, 
            preroll_len : int = 63500, url = None) -> None:
        self._byte_buffer = ByteBuffer(buffer_size)
        self._preroll_len = preroll_len

        if url is None:
            self._getURL(attempts=attempts)
        else:
            self._url = url

        super().__init__(daemon=True)

    def _getURL(self, attempts : int = 3) -> None:
        for i in range(0, attempts):
            try:
                self._url = get_stream_url()
                if self._url is not None:
                    break
            except TimeoutException:
                log.debug(f"Failed to get stream URL: Attempt #{i + 1}")

        if self._url is None:
            log.warning(f"Ran out of attempts to get stream url")
            raise RuntimeError("Failed to get a stream URL")

    def run(self) -> None:
        with request('GET', self._url, stream=True) as r:
            self._http_stream : HTTPResponse = r.raw

            # Dump preroll data
            with open(devnull, 'wb') as f:
                f.write(self._http_stream.read(self._preroll_len))

            while not self._http_stream.isclosed() and self._http_stream.readable():
                self._byte_buffer.append(self._http_stream.read(8192))
    
    def stop(self) -> None:
        if not self._http_stream.closed:
            self._http_stream.close()

    def __del__(self):
        if self._http_stream is not None and not self._http_stream.isclosed():
            self._http_stream.close()

class RadioStreamManager(Thread):
    _primary_radio_stream : RadioStream = None
    _redundant_radio_streams : List[RadioStream] = None
    _radio_stream_lock : RLock = None
    _desired_redundancy : int = 2
    _desired_buffer_size : int = 307200
    _stream_start_attempts : int = 3
    _stream_failover_handlers : \
        List[Callable[[RadioStream, RadioStream], None]] = None

    def __init__(self, redundancy : int = 2, buffer_size : int = 307200, 
            start_attempts : int = 3,
            on_stream_failover : Callable[[RadioStream, RadioStream], None] = None) -> None:
        if redundancy < 1:
            raise ValueError('Cannot have a redundancy less than 1')

        self._redundant_radio_streams = []
        self._radio_stream_lock = RLock()
        self._desired_redundancy = redundancy
        self._desired_buffer_size = buffer_size
        self._stream_start_attempts = start_attempts
        self._stream_failover_handlers = []
        
        if on_stream_failover is not None:
            self.add_stream_failover_handler(on_stream_failover)
        
        super().__init__(daemon=True)
    
    def _start_new_stream(self) -> RadioStream:
        result = None
        while result is None:
            try:
                result = RadioStream(self._desired_buffer_size, self._stream_start_attempts)
                result.start()
            except TimeoutException:
                log.debug("RadioStream failed to start due to TimeoutException. Will try again.")
        return result

    def _restore_redundancy(self):
        with self._radio_stream_lock:
            # Prune dead streams
            for stream in self._redundant_radio_streams:
                if not stream.is_alive():
                    self._redundant_radio_streams.remove(stream)
            
            # Start up new streams
            new_streams_needed = self._desired_redundancy - \
                                    len(self._redundant_radio_streams)
            for i in range(0, new_streams_needed):
                self._redundant_radio_streams.append(self._start_new_stream())

    def _replace_primary_stream(self):
        with self._radio_stream_lock:
            failover_stream : RadioStream = None
            for stream in self._redundant_radio_streams:
                if stream.is_alive():
                    failover_stream = stream
                    self._redundant_radio_streams.remove(stream)
                    break
            
            if failover_stream is None:
                # If all the redundant streams were dead, too, just
                # make a new stream
                failover_stream = self._start_new_stream()
            
            # Don't call handlers unless we're actually failing over
            if self._primary_radio_stream is not None:
                for handler in self._stream_failover_handlers:
                    handler(self._primary_radio_stream, failover_stream)
            
            self._primary_radio_stream = failover_stream

    def run(self):
        event = Event()
        while True:
            prs = self._primary_radio_stream
            if prs is None or not prs.is_alive():
                self._replace_primary_stream()
            self._restore_redundancy()
            event.wait(.250)
    
    @property
    def primary_radio_stream(self) -> RadioStream:
        with self._radio_stream_lock:
            return self._primary_radio_stream
  
    # First param of callable is old stream, second is new
    def add_stream_failover_handler(self, handler : Callable[[RadioStream, RadioStream], None]):
        if callable(handler) and handler not in self._stream_failover_handlers:
            self._stream_failover_handlers.append(handler)
    
    def remove_stream_failover_handler(self, handler: Callable[[RadioStream, RadioStream], None]):
        if handler in self._stream_failover_handlers:
            self._stream_failover_handlers.remove(handler)

class RedundantRadioStream(Thread):
    _byte_buffer : ByteBuffer = None
    _write_lock : RLock = None
    _radio_stream_manager : RadioStreamManager = None
    _sync_len : int = 10000
    _desired_stream_cache_len : int = 200000

    def __init__(self, redundancy : int = 2, buffer_size : int = 307200, 
            start_attempts : int = 3, sync_len : int = 10000,
            desired_stream_cache_len : int = 200000) -> None:
        self._byte_buffer = ByteBuffer(buffer_size)
        self._write_lock = RLock()
        self._sync_len = sync_len
        self._desired_stream_cache_len = desired_stream_cache_len

        self._radio_stream_manager = RadioStreamManager(redundancy, buffer_size, 
                                        start_attempts, daemon=True)

        super().__init__(daemon=True)

    @property
    def byte_buffer(self):
        return self._byte_buffer
    
    def run(self):
        if not self._radio_stream_manager.is_alive():
            self._radio_stream_manager.run()

        # TODO: Read a bit, write it to the main buffer
        event = Event()

        prs = self._radio_stream_manager.primary_radio_stream
        with self._write_lock:
            self.byte_buffer.append(prs.byte_buffer.readUpToRemainingLength(
                self._desired_stream_cache_len))
        event.wait(.250)

    def handleFailover(self, old_primary : RadioStream, new_primary : RadioStream) -> None:
        try:
            log.debug("Acquiring write lock")
            self._write_lock.acquire()
            log.debug("Write lock acquired")

            # Ensure 30% of the desired cache length remains.
            readLen = int(self._desired_stream_cache_len * 0.3)
            self.byte_buffer.append(old_primary.byte_buffer.readUpToRemainingLength(readLen))

            syncBytes = self.byte_buffer.readFromEnd(self._sync_len, consume=False)

            # If the new primary doesn't already have the sync bytes in it,
            # it probably never will. So only try once.
            try:
                new_primary.byte_buffer.seekPastSequence(syncBytes)
                log.debug("Successfuly synced new primary stream!")
            except ValueError:
                log.warning(f"Failed to sync new primary stream", exc_info=True)
                log.warning("Data will just be appended normally. This may " + 
                    "result in a \"jump\" in the recording.")
            
        finally:
            log.debug("Releasing write lock")
            self._write_lock.release()

