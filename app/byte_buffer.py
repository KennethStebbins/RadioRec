from threading import Lock

class ByteBuffer:
    byte_array : bytearray = None
    byte_array_lock : Lock = None
    length : int = 0
    index : int = 0
    max_index : int = 0

    def __init__(self, length : int=307200) -> None:
        self.byte_array = bytearray(length)
        self.byte_array_lock = Lock()
        self.length = len(self.byte_array)
    
    def append(self, b : bytes) -> None:
        try:
            self.byte_array_lock.acquire()

            b_len = len(b)
            bi = 0

            if b_len > self.length:
                # If the given bytes sequence is longer than our max length
                bi = b_len - self.length

            if b_len - bi + self.index > self.length:
                # If we need to wrap around
                first_pass_len = self.length - self.index
                self.byte_array[self.index:] = b[bi:bi + first_pass_len]
                
                self.max_index = self.length - 1 # Max out the max index
                self.index = 0
                bi = bi + first_pass_len
            
            b_remaining = b_len - bi
            self.byte_array[self.index:self.index + b_remaining] = b[bi:]

            self.index = self.index + b_remaining
            if self.index == self.length:
                self.index = 0
                self.max_index = self.length - 1
            elif self.max_index < self.index:
                self.max_index = self.index - 1
        finally:
            self.byte_array_lock.release()

    def read(self, length : int = -1) -> bytearray:
        if length > self.length:
            raise ValueError('Requested length is longer than the buffer length')
        elif length > self.max_index + 1:
            raise ValueError('Attempted to read more data than what exists in the buffer')
            
        try:
            self.byte_array_lock.acquire()
            
            if length < 0:
                length = self.max_index + 1

            readi = self.index

            response : bytearray = bytearray(length)
            responsei = 0     

            if self.max_index + 1 < self.length:
                # If we haven't filled the buffer yet, we need to read from index 0
                # instead of the current index
                readi = 0
            elif length + self.index > self.length:  
                # If we need to wrap around
                first_pass_len = self.length - self.index
                response[responsei:first_pass_len] = self.byte_array[self.index:]
                responsei = responsei + first_pass_len
                readi = 0
            
            response_remaining = length - responsei
            response[responsei:] = self.byte_array[readi:readi + response_remaining]

            return response
        except:
            self.byte_array_lock.release()
