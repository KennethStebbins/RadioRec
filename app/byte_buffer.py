from __future__ import annotations
from threading import Event, RLock
from typing import Tuple
import logging

log = logging.getLogger('RadioRec')

class ByteBuffer:
    _byte_array : bytearray = None
    _write_lock : RLock = None
    _consume_lock : RLock = None
    _length : int = 0
    _index : int = 0
    _read_index : int = 0
    _readable_length : int = 0

    @property
    def byte_array(self):
        return self._byte_array
    
    @property
    def length(self):
        return self.length
    
    @property
    def readable_length(self):
        return self._readable_length

    def __init__(self, length : int=307200) -> None:
        self._byte_array = bytearray(length)
        self._write_lock = RLock()
        self._consume_lock = RLock()
        self._length = len(self._byte_array)
        log.debug(f"ByteBuffer with length {self._length} created")
    
    def append(self, b : bytes) -> None:
        log.debug(f"ByteBuffer.append() called")
        try:
            log.debug("Acquiring byte array lock")
            self._write_lock.acquire()
            log.debug("Byte array lock acquired")

            b_len = len(b)
            log.debug(f"Given bytes length: {b_len}")
            bi = 0

            if b_len > self._length:
                # If the given bytes sequence is longer than our max length
                bi = b_len - self._length
            log.debug(f"bi is {bi}")

            log.debug(f"Old readable length: {self._readable_length}")
            if b_len + self._readable_length > self._length:
                self._readable_length = self._length
            else:
                self._readable_length += b_len
            log.debug(f"New readable length {self._readable_length}")

            if b_len - bi + self._index > self._length:
                log.debug(f"Will need to wrap")
                # If we need to wrap around
                first_pass_len = self._length - self._index
                log.debug(f"First pass length: {first_pass_len}")

                self._byte_array[self._index:] = b[bi:bi + first_pass_len]
                log.debug("First pass bytes written")

                self._index = 0
                bi = bi + first_pass_len
            
            b_remaining = b_len - bi
            log.debug(f"Bytes remaining: {b_remaining}")
            self._byte_array[self._index:self._index + b_remaining] = b[bi:]
            log.debug("Remaining bytes written")

            self._index = self._index + b_remaining
            if self._index == self._length:
                self._index = 0
            log.debug(f"New self index: {self._index}")

        finally:
            self._write_lock.release()
            log.debug("Byte array lock released")

    def _getFirstReadIndex(self) -> int:
        readi = self._index - self._readable_length
        if readi < 0:
            readi += self._length
        return readi
    
    def _getReadIndexFromEnd(self, length_from_end : int) -> int:
        readi = self._index - length_from_end
        if readi < 0:
            readi += self._length
        return readi

    def _findStopIndex(self, start : int, length : int) -> int:
        if start < 0:
            raise ValueError('Starting index cannot be negative')
        elif start >= self._length:
            raise ValueError('Start index exceeds buffer length')
        
        if length == 0:
            raise ValueError('Length cannot be zero')
        elif length < 0:
            raise ValueError('Length cannot be negative')
        elif length > self._length:
            raise ValueError('Requested length is longer than the buffer length')
        elif length > self._readable_length:
            raise ValueError('Requested length is longer than what exists in the buffer')
        
        stop = start + length - 1
        if stop >= self._length:
            stop -= self._length

        return stop
    
    def _getReadBounds(self) -> Tuple[int, int]:
        if self._readable_length == 0:
            raise ValueError('There is no readable data in the buffer')
        
        firstReadIndex = self._getFirstReadIndex()
        lastReadIndex = self._index - 1
        if lastReadIndex < 0:
            lastReadIndex = self._length - 1
        
        return (firstReadIndex, lastReadIndex)

    def _isWithinReadBounds(self, start : int, length : int) -> int:
        if start < 0:
            raise ValueError('Starting index cannot be negative')
        elif start >= self._length:
            raise ValueError('Start index exceeds buffer length')
        
        if length == 0:
            raise ValueError('Length cannot be zero')
        elif length < 0:
            raise ValueError('Length cannot be negative')
        elif length > self._length:
            raise ValueError('Requested length is longer than the buffer length')
        elif length > self._readable_length:
            raise ValueError('Requested length is longer than what exists in the buffer')

        firstReadIndex, lastReadIndex = self._getReadBounds()
        stop = self._findStopIndex(start, length)

        if lastReadIndex < firstReadIndex: # If the read range wraps
            return (start >= firstReadIndex or start <= lastReadIndex) and \
                (stop < self._length or stop <= lastReadIndex)
        else:
            return start >= firstReadIndex and stop <= lastReadIndex

    def _read(self, start : int, length : int, consume : bool = True) -> bytearray:
        log.debug(f"ByteBuffer._read() called. start: {start}, length: {length}, consume: {consume}")      
        if length == 0:
            log.debug("Requested read length was zero. Returning empty byte array.")
            return bytearray(b'')
        
        if not self._isWithinReadBounds(start, length):
            raise ValueError('Given start point and length are not within read bounds')
        log.debug("Requested read parameters are within bounds")

        try:
            log.debug("Acquiring write lock")
            self._write_lock.acquire()
            log.debug("Write lock acquired")

            if consume:
                log.debug("Acquiring consume lock")
                self._consume_lock.acquire()
                log.debug("Consume lock acquired")

            readi = start

            response : bytearray = bytearray(length)
            responsei = 0     

            if readi >= self._index:
                # If we might need to wrap around
                log.debug("We might need to wrap around")
                first_pass_len = self._length - readi
                if first_pass_len > length:
                    first_pass_len = length
                log.debug(f"First pass length: {first_pass_len}")

                response[responsei:first_pass_len] = self._byte_array[readi:]
                log.debug("First pass bytes written")

                responsei = responsei + first_pass_len
                readi = 0
            
            response_remaining = length - responsei
            log.debug(f"Response length remaining: {response_remaining}")
            response[responsei:] = self._byte_array[readi:readi + response_remaining]

            if consume:
                log.debug("Consuming")
                newReadingIndex = self._findStopIndex(start, length) + 1
                if newReadingIndex == self._length:
                    newReadingIndex = 0
                log.debug(f"New reading index: {newReadingIndex}")
                self._seekToIndex(newReadingIndex)

            return response
        finally:
            self._write_lock.release()
            log.debug("Write lock released")
            if consume:
                self._consume_lock.release()
                log.debug("Consume lock released")

    def read(self, length : int = -1, consume : bool = True) -> bytearray:        
        try:
            self._write_lock.acquire()
            if consume:
                self._consume_lock.acquire()
            start = self._getFirstReadIndex()

            if length < 0:
                length = self._readable_length
            
            return self._read(start, length, consume=consume)
        finally:
            self._write_lock.release()
            if consume:
                self._consume_lock.release()

    def readFromEnd(self, length : int, consume : bool = True) -> bytearray:
        if length == 0:
            raise ValueError("Length cannot be zero")
        elif length < 0:
            raise ValueError("Length cannot be negative")

        try:
            self._write_lock.acquire()
            if consume:
                self._consume_lock.acquire()

            start = self._getReadIndexFromEnd(length)
                
            return self._read(start, length, consume=consume)
        finally:
            self._write_lock.release()
            if consume:
                self._consume_lock.release()
    
    def readUpToRemainingLength(self, length : int, consume : bool = True) -> bytearray:
        if length < 0:
            raise ValueError("Length cannot be negative")
        elif self._readable_length < length:
            return bytearray(0)
        
        try:
            self._write_lock.acquire()
            if consume:
                self._consume_lock.acquire()

            readLength = self._readable_length - length

            return self.read(readLength, consume=consume)
        finally:
            self._write_lock.release()
            if consume:
                self._consume_lock.release()
    
    def waitUntilLengthAvailable(self, length : int) -> None:
        if length < 0:
            raise ValueError("Length cannot be negative")
        elif length > self._length:
            raise ValueError("Length is longer than buffer length")
        
        event = Event()
        with self._consume_lock:
            if self._readable_length >= length:
                return
            
            event.wait(0.25)
    
    def _seekTo(self, length : int, wait : bool = False) -> None:
        if length < 0:
            raise ValueError("Length cannot be negative")
        elif length > self._length:
            raise ValueError("Length is longer than buffer length")
        
        with self._write_lock, self._consume_lock:
            if length > self._readable_length:
                if wait:
                    self.waitUntilLengthAvailable(length)
                else:
                    raise ValueError("Length is longer than current readable length")
            
            self._readable_length = length

    def seek(self, length : int) -> None:
        if length < 0:
            raise ValueError('Cannot seek backwards')
        elif length > self._length:
            raise ValueError('Cannot seek further than the length of the buffer')
        
        with self._write_lock, self._consume_lock:
            if length > self._readable_length:
                raise ValueError("Cannot seek past the data stored in the buffer")

            self._seekTo(self._readable_length - length)

    def seekToEnd(self) -> None:
        self._seekTo(0)

    def _seekToIndex(self, index : int) -> None:
        log.debug(f"ByteArray._seekToIndex() called. index: {index}")
        if index < 0:
            raise ValueError('Index cannot be zero')
        elif index >= self._length:
            raise ValueError('Index exceeds buffer length')

        log.debug("Acquiring write and consume locks")
        with self._write_lock, self._consume_lock:
            log.debug("Byte array lock acquired")
            if index == self._index:
                log.debug("Given index matches the current index")
                self.seekToEnd()
            elif not self._isWithinReadBounds(index, 1):
                raise ValueError('Index is not within read bounds')
            elif index < self._index:
                log.debug("Given index is less than the current index")
                self._seekTo(self._index - index)
            else:
                log.debug("Given index is greater than the current index")
                self._seekTo(self._length - index + self._index)
        log.debug("Write and consume locks released")
    
    def _findSequence(self, seq : bytes, match_len_step : int = 1000):
        log.debug(f"ByteArray._findSequence called. match_len_step: {match_len_step}")
        seq_len = len(seq)
        log.debug(f"Sequence length: {seq_len}")
        if seq_len == 0:
            raise ValueError('Sequence cannot be empty')
        elif seq_len > self._length:
            raise ValueError('Sequence cannot be longer than buffer length')
        elif seq_len > self._readable_length:
            raise ValueError('Sequence is longer than readable length')

        try:
            seq = bytearray(seq)

            log.debug("Acquiring write lock")
            self._write_lock.acquire()
            log.debug("Write lock acquired")

            log.debug("Acquiring consume lock")
            self._consume_lock.acquire()
            log.debug("Consume acquired")

            firstReadi, lastReadi = self._getReadBounds()
            log.debug(f"Read bounds: [{firstReadi},{lastReadi}]")

            if firstReadi < lastReadi:
                possibleIndexes = range(firstReadi, lastReadi + 1)
            else:
                possibleIndexes = list(range(firstReadi, self._length))
                possibleIndexes += list(range(0, lastReadi + 1))
            
            matchingIndex = -1
            for i in possibleIndexes:
                log.debug(f"Evaluating starting index {i}")
                isMatch = True
                bestMatchLen = 0
                while isMatch and bestMatchLen < seq_len:
                    matchLen = bestMatchLen + match_len_step
                    if matchLen > seq_len:
                        matchLen = seq_len
                    log.debug(f"Current desired match length: {matchLen}")

                    readBytes = self._read(i, matchLen, consume=False)
                    isMatch = seq[:matchLen] == readBytes

                    bestMatchLen = matchLen

                    if not isMatch:
                        log.debug("Sequence did not match")
                        break
                    log.debug(f"Sequence matches!")
                
                if isMatch:
                    matchingIndex = i
                    log.debug(f"Match found at index {matchingIndex}")
                    break
            
            return matchingIndex

        finally:
            self._write_lock.release()
            log.debug("Byte array lock released")
            self._consume_lock.release()
            log.debug("Consume lock released")

    def seekToSequence(self, seq : bytes):
        with self._write_lock, self._consume_lock:
            index = self._findSequence(seq)
            
            if index >= 0:
                self._seekToIndex(index)
            else:
                raise ValueError('Sequence not found')

    def seekPastSequence(self, seq : bytes):
        with self._write_lock, self._consume_lock:
            index = self._findSequence(seq)
            
            if index >= 0:
                self._seekToIndex(index + len(seq))
            else:
                raise ValueError('Sequence not found')
