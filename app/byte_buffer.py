from threading import Lock

class ByteBuffer:
    byte_array : bytearray = None
    byte_array_lock : Lock = None
    length : int = 0
    index : int = 0
    read_index : int = 0
    readable_length : int = 0

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

    def read(self, length : int = -1) -> bytearray:
        if length > self.length:
            raise ValueError('Requested length is longer than the buffer length')
        elif length > self.readable_length:
            raise ValueError('Attempted to read more data than what exists in the buffer')
            
        try:
            self.byte_array_lock.acquire()
            
            if length < 0:
                length = self.readable_length

            readi = self.index - self.readable_length
            if readi < 0:
                readi += self.length

            response : bytearray = bytearray(length)
            responsei = 0     

            if length + self.index > self.length:  
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

    def seek(self, length : int):

        if length < 0:
            raise ValueError('Cannot seek backwards')
        elif length >= self.length:
            raise ValueError('Cannot seek further than the length of the buffer')
        elif self.index + length > self.readable_length:
            raise ValueError('Cannot seek past the data stored in the buffer')
        
        try:
            self.byte_array_lock.acquire()

            self.readable_length -= length
        finally:
            self.byte_array_lock.release()
