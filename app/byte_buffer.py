from threading import RLock
from typing import Tuple
import logging

log = logging.getLogger('RadioRec')

class ByteBuffer:
    byte_array : bytearray = None
    byte_array_lock : RLock = None
    length : int = 0
    index : int = 0
    read_index : int = 0
    readable_length : int = 0

    def __init__(self, length : int=307200) -> None:
        self.byte_array = bytearray(length)
        self.byte_array_lock = RLock()
        self.length = len(self.byte_array)
        log.debug(f"ByteBuffer with length {self.length} created")
    
    def append(self, b : bytes) -> None:
        log.debug(f"ByteBuffer.append() called")
        try:
            log.debug("Acquiring byte array lock")
            self.byte_array_lock.acquire()
            log.debug("Byte array lock acquired")

            b_len = len(b)
            log.debug(f"Given bytes length: {b_len}")
            bi = 0

            if b_len > self.length:
                # If the given bytes sequence is longer than our max length
                bi = b_len - self.length
            log.debug(f"bi is {bi}")

            log.debug(f"Old readable length: {self.readable_length}")
            if b_len + self.readable_length > self.length:
                self.readable_length = self.length
            else:
                self.readable_length += b_len
            log.debug(f"New readable length {self.readable_length}")

            if b_len - bi + self.index > self.length:
                log.debug(f"Will need to wrap")
                # If we need to wrap around
                first_pass_len = self.length - self.index
                log.debug(f"First pass length: {first_pass_len}")

                self.byte_array[self.index:] = b[bi:bi + first_pass_len]
                log.debug("First pass bytes written")

                self.index = 0
                bi = bi + first_pass_len
            
            b_remaining = b_len - bi
            log.debug(f"Bytes remaining: {b_remaining}")
            self.byte_array[self.index:self.index + b_remaining] = b[bi:]
            log.debug("Remaining bytes written")

            self.index = self.index + b_remaining
            if self.index == self.length:
                self.index = 0
            log.debug(f"New self index: {self.index}")

        finally:
            self.byte_array_lock.release()
            log.debug("Byte array lock released")

    def __getFirstReadIndex(self) -> int:
        with self.byte_array_lock:
            readi = self.index - self.readable_length
            if readi < 0:
                readi += self.length
            return readi
    
    def __getReadIndexFromEnd(self, length_from_end : int) -> int:
        with self.byte_array_lock:
            readi = self.index - length_from_end
            if readi < 0:
                readi += self.length
            return readi

    def __findStopIndex(self, start : int, length : int) -> int:
        if start < 0:
            raise ValueError('Starting index cannot be negative')
        elif start >= self.length:
            raise ValueError('Start index exceeds buffer length')
        
        if length == 0:
            raise ValueError('Length cannot be zero')
        elif length < 0:
            raise ValueError('Length cannot be negative')
        elif length > self.length:
            raise ValueError('Requested length is longer than the buffer length')
        elif length > self.readable_length:
            raise ValueError('Requested length is longer than what exists in the buffer')
        
        stop = start + length - 1
        if stop >= self.length:
            stop -= self.length

        return stop
    
    def __getReadBounds(self) -> Tuple[int, int]:
        if self.readable_length == 0:
            raise ValueError('There is no readable data in the buffer')
        
        firstReadIndex = self.__getFirstReadIndex()
        lastReadIndex = self.index - 1
        if lastReadIndex < 0:
            lastReadIndex = self.length - 1
        
        return (firstReadIndex, lastReadIndex)

    def __isWithinReadBounds(self, start : int, length : int) -> int:
        if start < 0:
            raise ValueError('Starting index cannot be negative')
        elif start >= self.length:
            raise ValueError('Start index exceeds buffer length')
        
        if length == 0:
            raise ValueError('Length cannot be zero')
        elif length < 0:
            raise ValueError('Length cannot be negative')
        elif length > self.length:
            raise ValueError('Requested length is longer than the buffer length')
        elif length > self.readable_length:
            raise ValueError('Requested length is longer than what exists in the buffer')

        with self.byte_array_lock:
            firstReadIndex, lastReadIndex = self.__getReadBounds()
            stop = self.__findStopIndex(start, length)

            if lastReadIndex < firstReadIndex: # If the read range wraps
                return (start >= firstReadIndex or start <= lastReadIndex) and \
                    (stop < self.length or stop <= lastReadIndex)
            else:
                return start >= firstReadIndex and stop <= lastReadIndex

    def __read(self, start : int, length : int, consume : bool = True) -> bytearray:
        log.debug(f"ByteBuffer.__read() called. start: {start}, length: {length}, consume: {consume}")      
        if length == 0:
            log.debug("Requested read length was zero. Returning empty byte array.")
            return bytearray(b'')
        
        if not self.__isWithinReadBounds(start, length):
            raise ValueError('Given start point and length are not within read bounds')
        log.debug("Requested read parameters are within bounds")

        try:
            log.debug("Acquiring byte array lock")
            self.byte_array_lock.acquire()
            log.debug("Byte array lock acquired")

            readi = start

            response : bytearray = bytearray(length)
            responsei = 0     

            if readi >= self.index:
                # If we might need to wrap around
                log.debug("We might need to wrap around")
                first_pass_len = self.length - readi
                if first_pass_len > length:
                    first_pass_len = length
                log.debug(f"First pass length: {first_pass_len}")

                response[responsei:first_pass_len] = self.byte_array[readi:]
                log.debug("First pass bytes written")

                responsei = responsei + first_pass_len
                readi = 0
            
            response_remaining = length - responsei
            log.debug(f"Response length remaining: {response_remaining}")
            response[responsei:] = self.byte_array[readi:readi + response_remaining]

            if consume:
                log.debug("Consuming")
                newReadingIndex = self.__findStopIndex(start, length) + 1
                if newReadingIndex == self.length:
                    newReadingIndex = 0
                log.debug(f"New reading index: {newReadingIndex}")
                self.__seekToIndex(newReadingIndex)

            return response
        finally:
            self.byte_array_lock.release()
            log.debug("Byte array lock released")

    def read(self, length : int = -1, consume : bool = True) -> bytearray:        
        with self.byte_array_lock:
            start = self.__getFirstReadIndex()

            if length < 0:
                length = self.readable_length
            
            return self.__read(start, length, consume=consume)


    def readFromEnd(self, length : int, consume : bool = True) -> bytearray:
        if length == 0:
            raise ValueError("Length cannot be zero")
        elif length < 0:
            raise ValueError("Length cannot be negative")

        with self.byte_array_lock:
            start = self.__getReadIndexFromEnd(length)
                
            return self.__read(start, length, consume=consume)

    def seek(self, length : int) -> None:
        if length < 0:
            raise ValueError('Cannot seek backwards')
        elif length > self.length:
            raise ValueError('Cannot seek further than the length of the buffer')
        elif length > self.readable_length:
            raise ValueError('Cannot seek past the data stored in the buffer')
        
        with self.byte_array_lock:
            self.readable_length -= length

    def seekToEnd(self) -> None:
        with self.byte_array_lock:
            self.seek(self.readable_length)

    def __seekToIndex(self, index : int) -> None:
        log.debug(f"ByteArray.__seekToIndex() called. index: {index}")
        if index < 0:
            raise ValueError('Index cannot be zero')
        elif index >= self.length:
            raise ValueError('Index exceeds buffer length')

        log.debug("Acquiring byte array lock")
        with self.byte_array_lock:
            log.debug("Byte array lock acquired")
            if index == self.index:
                log.debug("Given index matches the current index")
                self.readable_length = 0
            elif not self.__isWithinReadBounds(index, 1):
                raise ValueError('Index is not within read bounds')
            elif index < self.index:
                log.debug("Given index is less than the current index")
                self.readable_length = self.index - index
            else:
                log.debug("Given index is greater than the current index")
                self.readable_length = self.length - index + self.index
        log.debug("Byte array lock released")
    
    def __findSequence(self, seq : bytes, match_len_step : int = 1000):
        log.debug(f"ByteArray.__findSequence called. match_len_step: {match_len_step}")
        seq_len = len(seq)
        log.debug(f"Sequence length: {seq_len}")
        if seq_len == 0:
            raise ValueError('Sequence cannot be empty')
        elif seq_len > self.length:
            raise ValueError('Sequence cannot be longer than buffer length')
        elif seq_len > self.readable_length:
            raise ValueError('Sequence is longer than readable length')

        try:
            seq = bytearray(seq)

            log.debug("Acquiring byte array lock")
            self.byte_array_lock.acquire()
            log.debug("Byte array lock acquired")

            firstReadi, lastReadi = self.__getReadBounds()
            log.debug(f"Read bounds: [{firstReadi},{lastReadi}]")

            if firstReadi < lastReadi:
                possibleIndexes = range(firstReadi, lastReadi + 1)
            else:
                possibleIndexes = list(range(firstReadi, self.length))
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

                    readBytes = self.__read(i, matchLen, consume=False)
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
            self.byte_array_lock.release()
            log.debug("Byte array lock released")

    def seekToSequence(self, seq : bytes):
        with self.byte_array_lock:
            index = self.__findSequence(seq)
            
            if index >= 0:
                self.__seekToIndex(index)
            else:
                raise ValueError('Sequence not found')
