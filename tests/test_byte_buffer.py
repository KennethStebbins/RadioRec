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
        self.assertEqual(self.bb.max_index, 4)
        self.assertEqual(self.bb.index, 5)

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
        expected = b'23456789AB'

        self.bb.append(data)

        self.assertSequenceEqual(self.bb.byte_array, expected)

class TestByteBufferOversizedOverflowAppend(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_oversized_overflow_append(self):
        data = b'123456789AB'
        expected = b'456789AB23'

        self.bb.append(data)

        self.assertSequenceEqual(self.bb.byte_array, expected)

class TestByteBufferFullRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_full_read(self):
        expected = b'LUZ_NOCEDA'

        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferMiddleRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'WILLOW')
        self.bb.append(b'THEWITCH')
        # Expected byte buffer state: ITCHOWTHEW
    
    def test_middle_read(self):
        expected = b'OWTHE'

        result = self.bb.read(5)

        self.assertSequenceEqual(result, expected)

class TestByteBufferNotFullRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'King')
    
    def test_not_full_read(self):
        expected = b'King'

        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferWraparoundRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'AMITYBLIGHT')
    
    def test_wraparound_read(self):
        expected = b'MITYBLIGHT'

        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferOversizedRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'OWLLADYEDA')
    
    def test_oversized_read(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.read(11)

        self.assertEqual(cm.exception.args[0], 
            'Requested length is longer than the buffer length')

class TestByteBufferOversizedNotFullRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'Gus')
    
    def test_oversized_read(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.read(4)

        self.assertEqual(cm.exception.args[0], 
            'Attempted to read more data than what exists in the buffer')

if __name__ == '__main__':
    unittest.main()