import logging
from os import devnull
from requests import request
from selenium.common.exceptions import TimeoutException
from urllib3.response import HTTPResponse
from threading import Event, RLock, Thread
from typing import Callable, List
from datetime import datetime, timedelta

from app.get_stream_url import get_stream_url
from app.byte_buffer import ByteBuffer, PersistentByteBuffer

log = logging.getLogger('RadioRec')

class RadioStream(Thread):
    _byte_buffer : ByteBuffer = None
    _stream_url : str = None
    _preroll_len : int = 63500
    _http_stream : HTTPResponse = None
    _start_date: datetime = None
    
    @property
    def byte_buffer(self):
        return self._byte_buffer
    
    @property
    def stream_url(self):
        return self._stream_url
    
    @property
    def start_date(self):
        return self._start_date

    def __init__(self, page_url : str = None, buffer_size : int = 307200, 
            attempts : int = 3, preroll_len : int = 63500,
            stream_url : str = None) -> None:
        self._byte_buffer = ByteBuffer(buffer_size)
        self._preroll_len = preroll_len

        if stream_url is None:
            if page_url is None:
                raise ValueError("Must provide either page_url or stream_url")
            
            self._getURL(page_url, attempts=attempts)
        else:
            self._stream_url = stream_url

        self._start_date = datetime.now()

        super().__init__(daemon=True)

    def _getURL(self, page_url : str, attempts : int = 3) -> None:
        for i in range(0, attempts):
            try:
                self._stream_url = get_stream_url(page_url=page_url)
                if self._stream_url is not None:
                    break
            except TimeoutException:
                log.debug(f"Failed to get stream URL: Attempt #{i + 1}")

        if self._stream_url is None:
            log.warning(f"Ran out of attempts to get stream url")
            raise RuntimeError("Failed to get a stream URL")

    def run(self) -> None:
        with request('GET', self._stream_url, stream=True) as r:
            self._http_stream : HTTPResponse = r.raw

            # Dump preroll data
            with open(devnull, 'wb') as f:
                f.write(self._http_stream.read(self._preroll_len))

            while not self._http_stream.isclosed() and self._http_stream.readable():
                self._byte_buffer.append(self._http_stream.read(8192))
    
    def stop(self) -> None:
        if self._http_stream is not None and not self._http_stream.closed:
            self._http_stream.close()

    def __del__(self):
        if self._http_stream is not None and not self._http_stream.isclosed():
            self._http_stream.close()

class RadioStreamManager(Thread):
    _primary_radio_stream : RadioStream = None
    _redundant_radio_streams : List[RadioStream] = None
    _radio_stream_lock : RLock = None
    _page_url : str = None
    _desired_redundancy : int = 2
    _desired_buffer_size : int = 307200
    _desired_redundant_max_age_sec : int = 0
    _stream_start_attempts : int = 3
    _stream_failover_handlers : \
        List[Callable[[RadioStream, RadioStream], None]] = None

    def __init__(self, page_url : str, redundancy : int = 2, 
            buffer_size : int = 307200, start_attempts : int = 3,
            redundant_max_age_sec : int = 0,
            on_stream_failover : Callable[[RadioStream, RadioStream], None] = None) -> None:
        if redundancy < 1:
            raise ValueError('Cannot have a redundancy less than 1')

        self._redundant_radio_streams = []
        self._radio_stream_lock = RLock()
        self._stream_failover_handlers = []

        self._page_url = page_url
        self._desired_redundancy = redundancy
        self._desired_buffer_size = buffer_size
        self._stream_start_attempts = start_attempts
        self._desired_redundant_max_age_sec = redundant_max_age_sec
        
        if on_stream_failover is not None:
            self.add_stream_failover_handler(on_stream_failover)
        
        super().__init__(daemon=True)
    
    def _start_new_stream(self) -> RadioStream:
        result = None
        while result is None:
            try:
                result = RadioStream(self._page_url, 
                            buffer_size=self._desired_buffer_size, 
                            attempts=self._stream_start_attempts)
                result.start()
            except TimeoutException:
                log.debug("RadioStream failed to start due to TimeoutException. Will try again.")
        return result

    def _restore_redundancy(self):
        max_age = timedelta(seconds=self._desired_redundant_max_age_sec)
        now = datetime.now()

        with self._radio_stream_lock:
            # Prune dead streams
            for stream in self._redundant_radio_streams:
                if not stream.is_alive():
                    self._redundant_radio_streams.remove(stream)
            
            # Prune aged-out streams
            for stream in self._redundant_radio_streams:
                if (    len(self._redundant_radio_streams) > 1
                            or self._desired_redundancy < 2
                        ) \
                        and now - stream.start_date > max_age:
                    stream.stop()
                    self._redundant_radio_streams.remove(stream)
 
            # Start up new streams
            new_streams_needed = self._desired_redundancy - \
                                    len(self._redundant_radio_streams)

            if new_streams_needed > 0:
                log.debug(f"{new_streams_needed} redundant radio streams have failed.")

            for i in range(0, new_streams_needed):
                self._redundant_radio_streams.append(self._start_new_stream())

    def _replace_primary_stream(self):
        with self._radio_stream_lock:
            failover_stream : RadioStream = None
            for stream in self._redundant_radio_streams:
                if stream.is_alive() and \
                        (
                            failover_stream is None or
                            failover_stream.byte_buffer.readable_length <
                                stream.byte_buffer.readable_length
                        ):
                    failover_stream = stream
                    
            
            if failover_stream is None:
                # If all the redundant streams were dead, too, just
                # make a new stream
                log.warning("All radio streams have failed.")
                failover_stream = self._start_new_stream()
            else:
                self._redundant_radio_streams.remove(failover_stream)

            
            oldPRS = self._primary_radio_stream
            self._primary_radio_stream = failover_stream
            
            # Don't call handlers unless we're actually failing over
            if oldPRS is not None:
                for handler in self._stream_failover_handlers:
                    handler(oldPRS, failover_stream)
            

    def run(self):
        event = Event()
        while True:
            prs = self._primary_radio_stream
            if prs is None or not prs.is_alive():
                log.debug(f"Primary stream failed. Replacing...")
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
    _should_run : bool = True

    def __init__(self, page_url : str, redundancy : int = 2, 
            redundant_buffer_size : int = 307200,
            byte_buffer : ByteBuffer = None,
            cache_buffer_size : int = 307200, start_attempts : int = 3, 
            redundant_max_age_sec : int = 0, sync_len : int = 10000) -> None:
        if byte_buffer is None:
            self._byte_buffer = ByteBuffer(redundant_buffer_size)
        else:
            self._byte_buffer = byte_buffer

        if sync_len > self.byte_buffer.length or \
                sync_len > cache_buffer_size:
            raise ValueError("Sync length cannot be larger than the " + 
                    "redundant or cache buffer lengths")

        self._write_lock = RLock()
        self._sync_len = sync_len
        self._should_run = True

        self._radio_stream_manager = RadioStreamManager(page_url, 
                                        redundancy=redundancy, 
                                        buffer_size=cache_buffer_size, 
                                        start_attempts=start_attempts,
                                        redundant_max_age_sec=redundant_max_age_sec)
        self._radio_stream_manager.add_stream_failover_handler(
            self.handleFailover)

        super().__init__(daemon=True)

    @property
    def byte_buffer(self):
        return self._byte_buffer
    
    def run(self):
        if not self._radio_stream_manager.is_alive():
            self._radio_stream_manager.start()

        # TODO: Read a bit, write it to the main buffer
        event = Event()

        while self._should_run:
            rsm = self._radio_stream_manager
            if rsm.primary_radio_stream is None:
                event.wait(.250)
                continue

            with self._write_lock:
                self.byte_buffer.append(
                    rsm.primary_radio_stream.byte_buffer
                        .readUpToRemainingLength(
                            self._sync_len
                        )
                )
            event.wait(.250)

    def handleFailover(self, old_primary : RadioStream, new_primary : RadioStream) -> None:
        try:
            self._write_lock.acquire()

            self.byte_buffer.append(
                old_primary.byte_buffer.readUpToRemainingLength(
                    self._sync_len
                )
            )

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
            self._write_lock.release()

    def stop(self) -> None:
        self._should_run = False

class PersistentRedundantRadioStream(RedundantRadioStream):
    def __init__(self, filepath : str, page_url : str, redundancy: int = 2, 
            persistent_buffer_size: int = 50000, 
            cache_buffer_size : int = 307200, overwrite : bool = False, 
            should_write : bool = True, start_attempts: int = 3, 
            redundant_max_age_sec : int = 0,
            sync_len: int = 10000) -> None:
        
        byteBuffer = PersistentByteBuffer(filepath, 
                        length=persistent_buffer_size, 
                        overwrite=overwrite, should_write=should_write)
        self._filepath = filepath

        super().__init__(page_url=page_url, redundancy=redundancy, 
            byte_buffer=byteBuffer, cache_buffer_size=cache_buffer_size, 
            start_attempts=start_attempts, sync_len=sync_len,
            redundant_max_age_sec=redundant_max_age_sec)
    
    @property
    def filepath(self) -> str:
        return self._byte_buffer.filepath

    @filepath.setter
    def filepath(self, value : str) -> None:
        self._byte_buffer.filepath = value
    
    @property
    def should_write(self) -> bool:
        return self._byte_buffer.should_write
    
    @should_write.setter
    def should_write(self, value : bool) -> None:
        self._byte_buffer.should_write = value


    def writeAll(self) -> None:
        self._byte_buffer.writeAll()