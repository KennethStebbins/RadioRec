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
        self.assertEqual(self.bb.readable_length, 5)
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

class TestByteBufferVeryOversizedAppend(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
    
    def test_very_oversized_append(self):
        data = b'123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        expected = b'QRSTUVWXYZ'

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

class TestByteBufferAlmostFullRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(11)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_almost_full_read(self):
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

class TestByteBufferNoConsumeMultipleReads(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(12)
        self.bb.append(b'WinterSchnee')
    
    def test_wraparound_read(self):
        firstResult = self.bb.read(consume=False)
        secondResult = self.bb.read(consume=False)

        self.assertSequenceEqual(firstResult, secondResult)

class TestByteBufferMultipleReads(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(11)
        self.bb.append(b'PyrrhaNikos')
    
    def test_multiple_reads(self):
        expected = (b'Pyrrha', b'Nikos')

        firstResult = self.bb.read(6)
        secondResult = self.bb.read(5)

        self.assertSequenceEqual(firstResult, expected[0])
        self.assertSequenceEqual(secondResult, expected[1])

class TestByteBufferOversizedMultipleAutomaticSizeReads(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(14)
        self.bb.append(b'PennyPolendina')
    
    def test_oversized_multiple_automatic_size_reads(self):
        expected = b''

        self.bb.read()
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)
        self.assertEqual(self.bb.readable_length, 0)

class TestByteBufferReadFromEnd(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_full_read(self):
        expected = b'NOCEDA'

        result = self.bb.readFromEnd(6)

        self.assertSequenceEqual(result, expected)
        self.assertEqual(self.bb.readable_length, 0)

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

class TestByteBufferOversizedErrorFromMulitpleReads(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(12)
        self.bb.append(b'NoraValkryie')
    
    def test_oversized_error_from_multiple_reads(self):
        self.bb.read()

        with self.assertRaises(ValueError) as cm:
            self.bb.read(1)

        self.assertEqual(cm.exception.args[0], 
            'Attempted to read more data than what exists in the buffer')

class TestByteBufferSeek(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'SSBumbleby')
    
    def test_seek(self):
        expected = b'by'

        self.bb.seek(8)
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferBackwardsSeek(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LilithClawthorne')
    
    def test_backwards_seek(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.seek(-1)

        self.assertEqual(cm.exception.args[0], 
            'Cannot seek backwards')

class TestByteBufferOverLengthSeek(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'blakebelladonna')
    
    def test_over_length_seek(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.seek(11)

        self.assertEqual(cm.exception.args[0], 
            'Cannot seek further than the length of the buffer')

class TestByteBufferOverReadableLengthSeek(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'RUBY')
    
    def test_over_length_seek(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.seek(5)

        self.assertEqual(cm.exception.args[0], 
            'Cannot seek past the data stored in the buffer')

class TestByteBufferSeekToEnd(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'BakedAlaska')
    
    def test_seek_to_end(self):
        expected = b'YangAndNeo'

        self.bb.seekToEnd()
        self.bb.append(b'YangAndNeo')
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferSeekToSeq(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(52)
        self.bb.append(b'Great, the gang\'s all here! Now we can die together!')
    
    def test_seek_to_sequence(self):
        expected = b'Now we can die together!'

        self.bb.seekToSequence(b'Now')
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferOversizedSeekToSequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(4)
        self.bb.append(b'RUBY')
    
    def test_oversized_seek_to_sequence(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.seekToSequence(b'RUBYROSE')

        self.assertEqual(cm.exception.args[0], 
            'Sequence is longer than buffer length')

class TestByteBufferOverReadLengthSeekToSequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'RUBY')
    
    def test_over_read_length_seek_to_sequence(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.seekToSequence(b'RUBYROSE')

        self.assertEqual(cm.exception.args[0], 
            'Sequence is longer than readable length')

class TestByteBufferSeekToEmptySequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'RUBY')
    
    def test_seek_to_empty_sequence(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.seekToSequence(b'')

        self.assertEqual(cm.exception.args[0], 
            'Sequence must not be empty')

if __name__ == '__main__':
    unittest.main()