from __future__ import annotations
from pathlib import Path
from threading import Event, RLock
from typing import Tuple
import logging, os

log = logging.getLogger('RadioRec')

class ByteBuffer:
    _byte_array : bytearray = None
    _byte_array_lock : RLock = None
    _length : int = 0
    _index : int = 0
    _readable_length : int = 0

    @property
    def byte_array(self):
        return self._byte_array
    
    @property
    def length(self):
        return self._length
    
    @property
    def readable_length(self):
        return self._readable_length
    
    def _setReadableLength(self, length : int) -> None:
        if length < 0:
            raise ValueError("Length cannot be negative")
        elif length > self._length:
            raise ValueError("Length is longer than buffer length")
        
        with self._byte_array_lock:
            self._readable_length = length

    def __init__(self, length : int=307200) -> None:
        self._byte_array = bytearray(length)
        self._byte_array_lock = RLock()
        self._length = len(self._byte_array)
    
    def append(self, b : bytes) -> None:
        try:
            self._byte_array_lock.acquire()

            b_len = len(b)
            bi = 0

            if b_len > self._length:
                # If the given bytes sequence is longer than our max length
                bi = b_len - self._length

            if b_len + self._readable_length > self._length:
                self._setReadableLength(self._length)
            else:
                self._setReadableLength(self._readable_length + b_len)

            if b_len - bi + self._index > self._length:
                # If we need to wrap around
                first_pass_len = self._length - self._index

                self._byte_array[self._index:] = b[bi:bi + first_pass_len]

                self._index = 0
                bi = bi + first_pass_len
            
            b_remaining = b_len - bi
            self._byte_array[self._index:self._index + b_remaining] = b[bi:]
            
            self._index = self._index + b_remaining
            if self._index == self._length:
                self._index = 0

        except TypeError as e:
            raise ValueError("Value given for \"bytes\" is not a bytes-like object.") from e
        finally:
            self._byte_array_lock.release()

    def _getFirstReadIndex(self) -> int:
        with self._byte_array_lock:
            readi = self._index - self._readable_length
            if readi < 0:
                readi += self._length
            return readi
    
    def _getReadIndexFromEnd(self, length_from_end : int) -> int:
        if length_from_end == 0:
            raise ValueError('Length cannot be zero')
        elif length_from_end < 0:
            raise ValueError('Length cannot be negative')
        elif length_from_end > self._length:
            raise ValueError('Requested length is longer than the buffer length')
        
        with self._byte_array_lock:
            if length_from_end > self._readable_length:
                raise ValueError('Requested length is longer than what exists in the buffer')
            
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
        
        with self._byte_array_lock:
            if length > self._readable_length:
                raise ValueError('Requested length is longer than what exists in the buffer')
            
            stop = start + length - 1
            if stop >= self._length:
                stop -= self._length

            return stop
    
    def _getReadBounds(self) -> Tuple[int, int]:
        with self._byte_array_lock:
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
        
        with self._byte_array_lock:
            if length > self._readable_length:
                raise ValueError('Requested length is longer than what exists in the buffer')

            firstReadIndex, lastReadIndex = self._getReadBounds()
            stop = self._findStopIndex(start, length)

            if lastReadIndex < firstReadIndex: # If the read range wraps
                return (start >= firstReadIndex or start <= lastReadIndex) and \
                    (stop < self._length or stop <= lastReadIndex)
            else:
                return start >= firstReadIndex and stop <= lastReadIndex

    def _read(self, start : int, length : int, consume : bool = True) -> bytearray:
        if length == 0:
            return bytearray(b'')
        
        if not self._isWithinReadBounds(start, length):
            raise ValueError('Given start point and length are not within read bounds')

        try:
            self._byte_array_lock.acquire()

            readi = start

            response : bytearray = bytearray(length)
            responsei = 0     

            if readi >= self._index:
                # If we might need to wrap around
                first_pass_len = self._length - readi
                if first_pass_len > length:
                    first_pass_len = length

                response[responsei:first_pass_len] = self._byte_array[readi:]

                responsei = responsei + first_pass_len
                readi = 0
            
            response_remaining = length - responsei
            response[responsei:] = self._byte_array[readi:readi + response_remaining]

            if consume:
                newReadingIndex = self._findStopIndex(start, length) + 1
                if newReadingIndex == self._length:
                    newReadingIndex = 0
                if newReadingIndex == self._index:
                    self.seekToEnd()
                else:
                    self._seekToIndex(newReadingIndex)

            return response
        finally:
            self._byte_array_lock.release()

    def read(self, length : int = -1, consume : bool = True) -> bytearray:        
        with self._byte_array_lock:
            start = self._getFirstReadIndex()

            if length < 0:
                length = self._readable_length
            
            return self._read(start, length, consume=consume)

    def readFromEnd(self, length : int, consume : bool = True) -> bytearray:
        if length == 0:
            raise ValueError("Length cannot be zero")
        elif length < 0:
            raise ValueError("Length cannot be negative")

        with self._byte_array_lock:
            start = self._getReadIndexFromEnd(length)
                
            return self._read(start, length, consume=consume)
    
    def readUpToRemainingLength(self, length : int, consume : bool = True) -> bytearray:
        if length < 0:
            raise ValueError("Length cannot be negative")
        elif length > self._length:
            raise ValueError("Requested length is longer than the buffer length")

        with self._byte_array_lock:            
            if length > self._readable_length:
                return bytearray(0)

            readLength = self._readable_length - length

            return self.read(readLength, consume=consume)

    def seek(self, length : int) -> None:
        if length < 0:
            raise ValueError('Cannot seek backwards')
        elif length > self._length:
            raise ValueError('Cannot seek further than the length of the buffer')
        
        with self._byte_array_lock:
            if length > self._readable_length:
                raise ValueError("Cannot seek past the data stored in the buffer")

            self._setReadableLength(self._readable_length - length)

    def seekToEnd(self) -> None:
        self._setReadableLength(0)

    def _seekToIndex(self, index : int) -> None:
        if index < 0:
            raise ValueError('Index cannot be zero')
        elif index >= self._length:
            raise ValueError('Index exceeds buffer length')

        with self._byte_array_lock:
            if not self._isWithinReadBounds(index, 1):
                raise ValueError('Index is not within read bounds')
            elif index < self._index:
                self._setReadableLength(self._index - index)
            else:
                self._setReadableLength(self._length - index + self._index)
    
    def _findSequence(self, seq : bytes, match_len_step : int = 1000):
        seq_len = len(seq)
        if seq_len == 0:
            raise ValueError('Sequence cannot be empty')
        elif seq_len > self._length:
            raise ValueError('Sequence cannot be longer than buffer length')

        try:
            seq = bytearray(seq)

            self._byte_array_lock.acquire()
            
            if seq_len > self._readable_length:
                raise ValueError('Sequence is longer than readable length')

            firstReadi, lastReadi = self._getReadBounds()

            if firstReadi < lastReadi:
                possibleIndexes = range(firstReadi, lastReadi + 1)
            else:
                possibleIndexes = list(range(firstReadi, self._length))
                possibleIndexes += list(range(0, lastReadi + 1))
            
            matchingIndex = -1
            for i in possibleIndexes:
                isMatch = True
                bestMatchLen = 0
                while isMatch and bestMatchLen < seq_len:
                    matchLen = bestMatchLen + match_len_step
                    if matchLen > seq_len:
                        matchLen = seq_len

                    if not self._isWithinReadBounds(i, matchLen):
                        # If the remaining untested data in the buffer is shorter
                        # than the given sequence, the given sequence cannot
                        # exist
                        isMatch = False
                        break

                    readBytes = self._read(i, matchLen, consume=False)
                    isMatch = seq[:matchLen] == readBytes

                    bestMatchLen = matchLen

                    if not isMatch:
                        break
                
                if isMatch:
                    matchingIndex = i
                    break
            
            if matchingIndex < 0:
                raise ValueError('Failed to find given byte sequence')

            return matchingIndex

        finally:
            self._byte_array_lock.release()

    def seekToSequence(self, seq : bytes):
        with self._byte_array_lock:
            self._seekToIndex(self._findSequence(seq))

    def seekPastSequence(self, seq : bytes):
        with self._byte_array_lock:
            self.seekToSequence(seq)
            self.seek(len(seq))

class PersistentByteBuffer(ByteBuffer):
    _filepath : str = None
    _should_write : bool = True
    _file_lock : RLock = None

    def __init__(self, filepath : str, length: int = 50000,
            overwrite : bool = False, should_write : bool = True) -> None:
        
        self._file_lock = RLock()

        self._filepath = os.path.realpath(filepath)
        self._should_write = should_write

        if os.path.isfile(self._filepath):
            if overwrite:
                os.remove(self._filepath)
            else:
                raise FileExistsError(f"A file already exists at {self._filepath}")
        
        # Create the file, also testing whether we can write there at all
        Path(self._filepath).touch()
        os.remove(self._filepath)

        super().__init__(length=length)
    
    @property
    def filepath(self) -> str:
        return self._filepath
    
    @filepath.setter
    def filepath(self, filepath : str) -> None:
        with self._file_lock:
            self._filepath = filepath
    
    @property
    def should_write(self) -> bool:
        return self._should_write
    
    @should_write.setter
    def should_write(self, value : bool) -> None:
        log.debug(f"Persistent Byte Buffer: Should write changed to {value}")
        self._should_write = value
        
    def _writeToFile(self, b : bytes) -> None:
        if not self._should_write:
            return

        with self._file_lock:
            try:
                with open(self._filepath, 'ab') as f:
                    f.write(b)
            except:
                log.exception(f"Error writing bytes to file {self._filepath}")
    
    def append(self, b : bytes) -> None:
        bLen = len(b)

        with self._byte_array_lock:
            newLen = self._readable_length + bLen

            if newLen > self.length:
                writeLen = newLen - self.length
            
                if writeLen > self._readable_length:
                    self._writeToFile(self.read())
                    self._writeToFile(b[:self.length * -1])
                else:
                    self._writeToFile(self.read(writeLen))
            
            super().append(b)

    def writeAll(self) -> None:
        self._writeToFile(self.read())
    