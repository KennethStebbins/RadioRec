from app.byte_buffer import ByteBuffer
import unittest

class TestByteBufferCreation(unittest.TestCase):
    def test_creation(self):
        bb = ByteBuffer()

        self.assertIsInstance(bb, ByteBuffer)

class TestByteBufferNormalAppend(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
    
    def test_normal_append(self):
        data = b'12345'

        self.bb.append(data)

        self.assertSequenceEqual(self.bb.byte_array[0:5], data)

class TestByteBufferAppendToFull(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_append_to_fill(self):
        data = b'12'
        expected = b'PREPARED12'

        self.bb.append(data)

        self.assertSequenceEqual(self.bb.byte_array, expected)

class TestByteBufferOverflowAppend(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_overflow_append(self):
        data = b'12345'
        expected = b'345PARED12'

        self.bb.append(data)

        self.assertSequenceEqual(self.bb.byte_array, expected)

class TestByteBufferOversizedAppend(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
    
    def test_oversized_append(self):
        data = b'123456789AB'
        expected = b'B23456789A'

        self.bb.append(data)

        self.assertSequenceEqual(self.bb.byte_array, expected)

class TestByteBufferOversizedOverflowAppend(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_oversized_append(self):
        data = b'123456789AB'
        expected = b'3456789AB2'

        self.bb.append(data)

        self.assertSequenceEqual(self.bb.byte_array, expected)

if __name__ == '__main__':
    unittest.main()