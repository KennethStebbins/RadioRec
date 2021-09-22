from threading import RLock
from typing import Tuple

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
    
    def append(self, b : bytes) -> None:
        try:
            self.byte_array_lock.acquire()

            b_len = len(b)
            bi = 0

            if b_len > self.length:
                # If the given bytes sequence is longer than our max length
                bi = b_len - self.length
            
            if b_len + self.readable_length > self.length:
                self.readable_length = self.length
            else:
                self.readable_length += b_len

            if b_len - bi + self.index > self.length:
                # If we need to wrap around
                first_pass_len = self.length - self.index
                self.byte_array[self.index:] = b[bi:bi + first_pass_len]
                
                self.index = 0
                bi = bi + first_pass_len
            
            b_remaining = b_len - bi
            self.byte_array[self.index:self.index + b_remaining] = b[bi:]

            self.index = self.index + b_remaining
            if self.index == self.length:
                self.index = 0

        finally:
            self.byte_array_lock.release()

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
        if stop + 1 > self.length:
            stop -= self.length

        return stop
    
    def __getReadBounds(self) -> Tuple[int, int]:
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
                return start >= firstReadIndex and \
                    (stop <= self.length or stop <= lastReadIndex)
            else:
                return start >= firstReadIndex and stop <= lastReadIndex

    def __read(self, start : int, length : int, consume : bool = True) -> bytearray:        
        if length == 0:
            return bytearray(b'')
        
        if not self.__isWithinReadBounds(start, length):
            raise ValueError('Given start point and length are not within read bounds')

        try:
            self.byte_array_lock.acquire()

            readi = start

            response : bytearray = bytearray(length)
            responsei = 0     

            if readi >= self.index:  
                # If we might need to wrap around
                first_pass_len = self.length - readi
                if first_pass_len > length:
                    first_pass_len = length
                response[responsei:first_pass_len] = self.byte_array[readi:]
                responsei = responsei + first_pass_len
                readi = 0
            
            response_remaining = length - responsei
            response[responsei:] = self.byte_array[readi:readi + response_remaining]

            if consume:
                newReadingIndex = self.__findStopIndex(start, length) + 1
                if newReadingIndex == self.length:
                    newReadingIndex = 0
                self.__seekToIndex(newReadingIndex)

            return response
        finally:
            self.byte_array_lock.release()

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
        if index < 0:
            raise ValueError('Index cannot be zero')
        elif index >= self.length:
            raise ValueError('Index exceeds buffer length')

        with self.byte_array_lock:
            if index == self.index:
                self.readable_length = 0
            elif not self.__isWithinReadBounds(index, 1):
                raise ValueError('Index is not within read bounds')
            elif self.index >= index:
                self.readable_length = self.index - index
            else:
                self.readable_length = self.length - index + self.index
    
    def __findSequence(self, seq : bytes):
        seq_len = len(seq)
        if seq_len == 0:
            raise ValueError('Sequence cannot be empty')
        elif seq_len > self.length:
            raise ValueError('Sequence cannot be longer than buffer length')
        elif seq_len > self.readable_length:
            raise ValueError('Sequence is longer than readable length')
        
        try:
            seq = bytearray(seq)

            self.byte_array_lock.acquire()

            firstReadi, lastReadi = self.__getReadBounds()

            if firstReadi < lastReadi:
                possibleIndexes = range(firstReadi, lastReadi + 1)
            else:
                possibleIndexes = list(range(firstReadi, self.length))
                possibleIndexes += list(range(0, lastReadi + 1))
            
            matchingIndex = -1
            for i in possibleIndexes:
                isMatch = True
                bestMatchLen = 0
                while isMatch and bestMatchLen < seq_len:
                    matchLen = bestMatchLen + 1
                    readBytes = self.__read(i, matchLen, consume=False)
                    isMatch = seq[:matchLen] == readBytes
                    bestMatchLen += 1
                    if not isMatch:
                        break
                
                if isMatch:
                    matchingIndex = i
                    break
            
            return matchingIndex

        finally:
            self.byte_array_lock.release()

    def seekToSequence(self, seq : bytes):        
        index = 0

        try:
            self.byte_array_lock.acquire()

            index = self.__findSequence(seq)
            
            if index >= 0:
                self.__seekToIndex(index)
            else:
                raise ValueError('Sequence not found')
        finally:
            self.byte_array_lock.release()
