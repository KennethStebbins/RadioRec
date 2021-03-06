from app.byte_buffer import ByteBuffer, PersistentByteBuffer
from pathlib import Path
import os, unittest

class TestByteBufferCreation(unittest.TestCase):
    def test_creation(self):
        bb = ByteBuffer()

        self.assertIsInstance(bb, ByteBuffer)
    
    def test_custom_len(self):
        expected = 10

        bb = ByteBuffer(length=10)

        self.assertIsInstance(bb, ByteBuffer)
        self.assertEqual(bb.length, expected)

class TestByteBufferByteArrayProperty(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
    
    def test_byte_array_property(self):
        self.assertEqual(self.bb.byte_array, self.bb._byte_array)

class TestByteBufferLengthProperty(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
    
    def test_byte_array_property(self):
        self.assertEqual(self.bb.length, self.bb._length)

class TestByteBufferReadableLengthProperty(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'BLAKE')
    
    def test_byte_array_property(self):
        self.assertEqual(self.bb.readable_length, self.bb._readable_length)

class TestByteBufferSetReadableLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'SSBumbleby')
    
    def test_set_readable_length(self):
        expected = b'Bumbleby'

        self.bb._setReadableLength(8)
        self.assertEqual(self.bb.readable_length, 8)

        result = self.bb.read()
        self.assertSequenceEqual(result, expected)

class TestByteBufferSetReadableLengthNegativeLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'SSBumbleby')
    
    def test_set_readable_length_negative_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._setReadableLength(-1)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be negative')

class TestByteBufferSetReadableLengthOverBufferLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'SSBumbleby')
    
    def test_set_readable_length_over_buffer_len_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._setReadableLength(11)

        self.assertEqual(cm.exception.args[0], 
            'Length is longer than buffer length')

class TestByteBufferNormalAppend(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
    
    def test_normal_append(self):
        data = b'12345'

        self.bb.append(data)

        self.assertSequenceEqual(self.bb.byte_array[0:5], data)
        self.assertEqual(self.bb.readable_length, 5)
        self.assertEqual(self.bb._index, 5)

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

class TestByteBufferAppendNonBytesData(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
    
    def test_find_stop_index_negative_start(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.append('hahaha')

        self.assertEqual(cm.exception.args[0], 
            'Value given for \"bytes\" is not a bytes-like object.')

class TestByteBufferGetFirstReadIndex(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_get_first_read_index(self):
        expected = 0

        result = self.bb._getFirstReadIndex()

        self.assertEqual(result, expected)

class TestByteBufferGetFirstReadIndexWrapped(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
        self.bb.append(b'READY')
    
    def test_get_first_read_index_wrapped(self):
        expected = 3

        result = self.bb._getFirstReadIndex()

        self.assertEqual(result, expected)

class TestByteBufferGetReadIndexFromEnd(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_get_read_index_from_end(self):
        expected = 3

        result = self.bb._getReadIndexFromEnd(5)

        self.assertEqual(result, expected)

class TestByteBufferGetReadIndexFromEndWrapped(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
        self.bb.append(b'READY')
    
    def test_get_read_index_from_end_wrapped(self):
        expected = 8

        result = self.bb._getReadIndexFromEnd(5)

        self.assertEqual(result, expected)

class TestByteBufferGetReadIndexFromEndFullBuffer(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_get_read_index_from_end_full_buffer(self):
        expected = 5

        result = self.bb._getReadIndexFromEnd(5)

        self.assertEqual(result, expected)

class TestByteBufferGetReadIndexFromEndFullLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_get_read_index_from_end_full_length(self):
        expected = 0

        result = self.bb._getReadIndexFromEnd(8)

        self.assertEqual(result, expected)

class TestByteBufferGetReadIndexFromEndZeroLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_get_read_index_from_end_zero_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._getReadIndexFromEnd(0)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be zero')

class TestByteBufferGetReadIndexFromEndNegativeLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_get_read_index_from_end_negative_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._getReadIndexFromEnd(-1)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be negative')

class TestByteBufferGetReadIndexFromEndOverBufferLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_get_read_index_from_end_over_buffer_len_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._getReadIndexFromEnd(11)

        self.assertEqual(cm.exception.args[0], 
            'Requested length is longer than the buffer length')

class TestByteBufferGetReadIndexFromEndOverReadableLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_get_read_index_from_end_over_readable_len_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._getReadIndexFromEnd(10)

        self.assertEqual(cm.exception.args[0], 
            'Requested length is longer than what exists in the buffer')

class TestByteBufferFindStopIndex(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_find_stop_index(self):
        expected = 2

        result = self.bb._findStopIndex(0, 3)

        self.assertEqual(result, expected)

class TestByteBufferFindStopIndexMaxReadable(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_find_stop_index_max_readable(self):
        expected = 7

        result = self.bb._findStopIndex(0, 8)

        self.assertEqual(result, expected)

class TestByteBufferFindStopIndexMax(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_find_stop_index_max(self):
        expected = 9

        result = self.bb._findStopIndex(0, 10)

        self.assertEqual(result, expected)

class TestByteBufferFindStopIndexWrapped(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
        self.bb.append(b'READY')
    
    def test_find_stop_index_wrapped(self):
        expected = 2

        result = self.bb._findStopIndex(8, 5)

        self.assertEqual(result, expected)

class TestByteBufferFindStopIndexWrappedMaxReadable(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
        self.bb.append(b'READY')
        self.bb.seek(3)
    
    def test_find_stop_index_wrapped_max_readable(self):
        expected = 2

        result = self.bb._findStopIndex(6, 7)

        self.assertEqual(result, expected)

class TestByteBufferFindStopIndexWrappedMax(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
        self.bb.append(b'READY')
    
    def test_find_stop_index_wrapped_max(self):
        expected = 2

        result = self.bb._findStopIndex(3, 10)

        self.assertEqual(result, expected)

class TestByteBufferFindStopIndexNegativeStart(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')    
    
    def test_find_stop_index_negative_start(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findStopIndex(-1, 5)

        self.assertEqual(cm.exception.args[0], 
            'Starting index cannot be negative')

class TestByteBufferFindStopIndexOversizedStart(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_find_stop_index_oversized_start(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findStopIndex(10, 5)

        self.assertEqual(cm.exception.args[0], 
            'Start index exceeds buffer length')

class TestByteBufferFindStopIndexZeroLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_find_stop_index_zero_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findStopIndex(0, 0)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be zero')

class TestByteBufferFindStopIndexNegativeLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_find_stop_index_negative_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findStopIndex(0, -1)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be negative')

class TestByteBufferFindStopIndexOverBufferLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_find_stop_index_over_buffer_len_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findStopIndex(0, 11)

        self.assertEqual(cm.exception.args[0], 
            'Requested length is longer than the buffer length')

class TestByteBufferFindStopIndexOverReadableLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_find_stop_index_over_readable_len_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findStopIndex(0, 9)

        self.assertEqual(cm.exception.args[0], 
            'Requested length is longer than what exists in the buffer')

class TestByteBufferGetReadBounds(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_get_read_bounds(self):
        expected = (0, 7)

        result = self.bb._getReadBounds()

        self.assertSequenceEqual(result, expected)

class TestByteBufferGetReadBoundsMax(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_get_read_bounds_max(self):
        expected = (0, 9)

        result = self.bb._getReadBounds()

        self.assertSequenceEqual(result, expected)

class TestByteBufferGetReadBoundsWrapped(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
        self.bb.append(b'READY')
    
    def test_get_read_bounds_wrapped(self):
        expected = (3, 2)

        result = self.bb._getReadBounds()

        self.assertSequenceEqual(result, expected)

class TestByteBufferGetReadBoundsNoData(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
    
    def test_get_read_bounds_no_data(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._getReadBounds()

        self.assertEqual(cm.exception.args[0], 
            'There is no readable data in the buffer')

class TestByteBufferGetReadBoundsAllDataConsumed(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
        self.bb.seek(10)
    
    def test_get_read_bounds_no_data(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._getReadBounds()

        self.assertEqual(cm.exception.args[0], 
            'There is no readable data in the buffer')

class TestByteBufferIsWithinReadBounds(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_is_within_read_bounds(self):
        expected = True

        result = self.bb._isWithinReadBounds(0, 6)

        self.assertEqual(result, expected)

class TestByteBufferIsWithinReadBoundsMaxReadable(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_is_within_read_bounds_max_readable(self):
        expected = True

        result = self.bb._isWithinReadBounds(0, 8)

        self.assertEqual(result, expected)

class TestByteBufferIsWithinReadBoundsMax(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_is_within_read_bounds_max(self):
        expected = True

        result = self.bb._isWithinReadBounds(0, 10)

        self.assertEqual(result, expected)

class TestByteBufferIsWithinReadBoundsNonzeroStart(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_is_within_read_bounds_nonzero_start(self):
        expected = True

        result = self.bb._isWithinReadBounds(3, 4)

        self.assertEqual(result, expected)

class TestByteBufferIsWithinReadBoundsWrapped(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
        self.bb.append(b'READY')
    
    def test_is_within_read_bounds_wrapped(self):
        expected = True

        result = self.bb._isWithinReadBounds(3, 8)

        self.assertEqual(result, expected)

class TestByteBufferIsWithinReadBoundsWrappedMax(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
        self.bb.append(b'READY')
    
    def test_is_within_read_bounds_wrapped_max(self):
        expected = True

        result = self.bb._isWithinReadBounds(3, 10)

        self.assertEqual(result, expected)

class TestByteBufferIsWithinReadBoundsNegativeStart(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_is_within_read_bounds_negative_start(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._isWithinReadBounds(-1, 5)

        self.assertEqual(cm.exception.args[0], 
            'Starting index cannot be negative')

class TestByteBufferIsWithinReadBoundsOversizedStart(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_is_within_read_bounds_oversized_start(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._isWithinReadBounds(11, 5)

        self.assertEqual(cm.exception.args[0], 
            'Start index exceeds buffer length')

class TestByteBufferIsWithinReadBoundsZeroLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_is_within_read_bounds_zero_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._isWithinReadBounds(0, 0)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be zero')

class TestByteBufferIsWithinReadBoundsNegativeLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_is_within_read_bounds_negative_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._isWithinReadBounds(0, -1)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be negative')

class TestByteBufferIsWithinReadBoundsOverBufferLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED!!')
    
    def test_is_within_read_bounds_negative_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._isWithinReadBounds(0, 11)

        self.assertEqual(cm.exception.args[0], 
            'Requested length is longer than the buffer length')

class TestByteBufferIsWithinReadBoundsOverReadableLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'PREPARED')
    
    def test_is_within_read_bounds_over_readable_len(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._isWithinReadBounds(0, 10)

        self.assertEqual(cm.exception.args[0], 
            'Requested length is longer than what exists in the buffer')

class TestByteBufferFullRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_full_read(self):
        expected = b'LUZ_NOCEDA'

        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferZeroLengthRead(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_zero_length_read(self):
        expected = b''

        result = self.bb.read(0)

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
            'Requested length is longer than what exists in the buffer')

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
            'Requested length is longer than what exists in the buffer')

class TestByteBufferReadFromEnd(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_read_from_end(self):
        expected = b'NOCEDA'

        result = self.bb.readFromEnd(6)

        self.assertSequenceEqual(result, expected)
        self.assertEqual(self.bb.readable_length, 0)

class TestByteBufferReadFromEndNoConsume(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_read_from_end_no_consume(self):
        expected = b'NOCEDA'

        result = self.bb.readFromEnd(6, consume=False)

        self.assertSequenceEqual(result, expected)
        self.assertEqual(self.bb.readable_length, 10)

class TestByteBufferZeroLengthReadFromEnd(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_zero_length_read_from_end(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.readFromEnd(0)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be zero')

class TestByteBufferNegativeReadFromEnd(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'OWLLADYEDA')
    
    def test_negative_read_from_end(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.readFromEnd(-1)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be negative')

class TestByteBufferReadUpToRemainingLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_read_up_to_remaining_length(self):
        expected = b'LUZ_'

        result = self.bb.readUpToRemainingLength(6)

        self.assertSequenceEqual(result, expected)
        self.assertEqual(self.bb.readable_length, 6)

class TestByteBufferReadUpToRemainingLengthNoConsume(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_read_up_to_remaining_length_no_consume(self):
        expected = b'LUZ_'

        result = self.bb.readUpToRemainingLength(6 ,consume=False)

        self.assertSequenceEqual(result, expected)
        self.assertEqual(self.bb.readable_length, 10)

class TestByteBufferReadUpToRemainingLengthOverReadableLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ')
    
    def test_read_up_to_remaining_length_over_readable_len_length(self):
        expected = b''

        result = self.bb.readUpToRemainingLength(6)

        self.assertSequenceEqual(result, expected)

class TestByteBufferReadUpToRemainingLengthNegativeLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_read_up_to_remaining_length_negative_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.readUpToRemainingLength(-1)

        self.assertEqual(cm.exception.args[0], 
            'Length cannot be negative')

class TestByteBufferReadUpToRemainingLengthOverBufferLenLength(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'LUZ_NOCEDA')
    
    def test_read_up_to_remaining_length_over_buffer_len_length(self):
        with self.assertRaises(ValueError) as cm:
            self.bb.readUpToRemainingLength(11)

        self.assertEqual(cm.exception.args[0], 
            'Requested length is longer than the buffer length')

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
        self.assertEqual(self.bb.readable_length, 0)

        self.bb.append(b'YangAndNeo')
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferSeekToIndex(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(11)
        self.bb.append(b'BakedAlaska')
    
    def test_seek_to_index(self):
        expected = b'Alaska'

        self.bb._seekToIndex(5)
        self.assertEqual(self.bb.readable_length, 6)

        result = self.bb.read()
        self.assertSequenceEqual(result, expected)

class TestByteBufferSeekToIndexWrapped(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(8)
        self.bb.append(b'Baked')
        self.bb.append(b'Alaska')
    
    def test_seek_to_index_wrapped(self):
        expected = b'Alaska'

        self.bb._seekToIndex(5)
        self.assertEqual(self.bb.readable_length, 6)

        result = self.bb.read()
        self.assertSequenceEqual(result, expected)

class TestByteBufferSeekToIndexNegativeIndex(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(11)
        self.bb.append(b'BakedAlaska')
    
    def test_seek_to_index_negative_index(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._seekToIndex(-1)

        self.assertEqual(cm.exception.args[0], 
            'Index cannot be zero')

class TestByteBufferSeekToIndexOverBufferLenIndex(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(11)
        self.bb.append(b'BakedAlaska')
    
    def test_seek_to_index_over_buffer_len_index(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._seekToIndex(11)

        self.assertEqual(cm.exception.args[0], 
            'Index exceeds buffer length')

class TestByteBufferSeekToIndexOutsideReadBoundsIndex(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(11)
        self.bb.append(b'BakedAlaska')
        self.bb.seek(5)
    
    def test_seek_to_index_over_buffer_len_index(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._seekToIndex(1)

        self.assertEqual(cm.exception.args[0], 
            'Index is not within read bounds')

class TestByteBufferSeekToIndexCurrentIndex(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(11)
        self.bb.append(b'BakedAlaska')
        self.bb.seek(5)
    
    def test_seek_to_index_current_index(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._seekToIndex(0)

        self.assertEqual(cm.exception.args[0], 
            'Index is not within read bounds')

class TestByteBufferFindSequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(52)
        self.bb.append(b'Great, the gang\'s all here! Now we can die together!')
    
    def test_find_sequence(self):
        expected = 28

        result = self.bb._findSequence(b'Now')
        self.assertEqual(result, expected)

class TestByteBufferFindSequenceWraparound(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(30)
        self.bb.append(b'Great, the gang\'s all here!')
        self.bb.append(b'Now we can die together!')
    
    def test_find_sequence_wraparound(self):
        expected = 12

        result = self.bb._findSequence(b'together')
        self.assertEqual(result, expected)

class TestByteBufferFindSequenceExactBufferLengthSeq(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(9)
        self.bb.append(b'Ruby Rose')
    
    def test_find_sequence_exact_buffer_length_seq(self):
        expected = 0

        result = self.bb._findSequence(b'Ruby Rose')
        self.assertEqual(result, expected)

class TestByteBufferFindSequenceExactReadableLengthSeq(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'Ruby Rose')
    
    def test_find_sequence_exact_readable_length_seq(self):
        expected = 0

        result = self.bb._findSequence(b'Ruby Rose')
        self.assertEqual(result, expected)

class TestByteBufferOversizedFindSequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(4)
        self.bb.append(b'RUBY')
    
    def test_oversized_find_sequence(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findSequence(b'RUBYROSE')

        self.assertEqual(cm.exception.args[0], 
            'Sequence cannot be longer than buffer length')

class TestByteBufferOverReadLengthFindSequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'RUBY')
    
    def test_over_read_length_find_sequence(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findSequence(b'RUBYROSE')

        self.assertEqual(cm.exception.args[0], 
            'Sequence is longer than readable length')

class TestByteBufferFindEmptySequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'RUBY')
    
    def test_find_empty_sequence(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findSequence(b'')

        self.assertEqual(cm.exception.args[0], 
            'Sequence cannot be empty')

class TestByteBufferFindNonexistentSequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(10)
        self.bb.append(b'RUBY')
    
    def test_find_nonexistent_sequence(self):
        with self.assertRaises(ValueError) as cm:
            self.bb._findSequence(b'ROSE')

        self.assertEqual(cm.exception.args[0], 
            'Failed to find given byte sequence')

class TestByteBufferSeekToSequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(52)
        self.bb.append(b'Great, the gang\'s all here! Now we can die together!')
    
    def test_seek_to_sequence(self):
        expected = b'Now we can die together!'

        self.bb.seekToSequence(b'Now')
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferSeekToSequenceWraparound(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(30)
        self.bb.append(b'Great, the gang\'s all here!')
        self.bb.append(b'Now we can die together!')
    
    def test_seek_to_sequence_wraparound(self):
        expected = b'Now we can die together!'

        self.bb.seekToSequence(b'Now')
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferSeekPastSequence(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(52)
        self.bb.append(b'Great, the gang\'s all here! Now we can die together!')
    
    def test_seek_past_sequence(self):
        expected = b'Now we can die together!'

        self.bb.seekPastSequence(b'here! ')
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestByteBufferSeekPastSequenceWraparound(unittest.TestCase):
    bb = None

    def setUp(self) -> None:
        self.bb = ByteBuffer(30)
        self.bb.append(b'Great, the gang\'s all here! ')
        self.bb.append(b'Now we can die together!')
    
    def test_seek_past_sequence_wraparound(self):
        expected = b'Now we can die together!'

        self.bb.seekPastSequence(b'here! ')
        result = self.bb.read()

        self.assertSequenceEqual(result, expected)

class TestPersistentByteBufferCreation(unittest.TestCase):

    def test_init(self) -> None:
        testFilePath : str = './tests/output/pbb_test_init'

        if os.path.isfile(testFilePath):
            os.remove(testFilePath)

        pbb = PersistentByteBuffer(testFilePath)

        self.assertIsInstance(pbb, PersistentByteBuffer)

    def test_init_overwrite(self) -> None:
        testFilePath : str = './tests/output/pbb_test_init_overwrite'

        with open(testFilePath, 'w') as f:
            f.write('This is some content!')

        pbb = PersistentByteBuffer(testFilePath, overwrite=True)

        self.assertIsInstance(pbb, PersistentByteBuffer)

        self.assertFalse(os.path.exists(testFilePath))
        
    def test_init_no_overwrite(self) -> None:
        testFilePath : str = './tests/output/pbb_test_init_no_overwrite'

        with open(testFilePath, 'w') as f:
            f.write('This is some content!')

        try:
            with self.assertRaises(FileExistsError) as cm:
                pbb = PersistentByteBuffer(testFilePath)

            self.assertEqual(cm.exception.args[0], 
                f"A file already exists at {os.path.realpath(testFilePath)}")
        finally:
            os.remove(testFilePath)

class TestPersistentByteBufferFunctions(unittest.TestCase):
    _pbb : PersistentByteBuffer = None
    _filepath : str = './tests/output/pbb_test_functions'

    def setUp(self) -> None:
        if os.path.isfile(self._filepath):
            os.remove(self._filepath)

        self._pbb = PersistentByteBuffer(self._filepath, 10)
    
    def tearDown(self) -> None:
        if os.path.isfile(self._filepath):
            os.remove(self._filepath)

    def test_filepath_property(self) -> None:
        self.assertEqual(self._pbb._filepath, self._pbb.filepath)
    
    def test_no_overflow_write(self) -> None:
        self._pbb.append(b'test!')

        self.assertFalse(os.path.exists(self._filepath))
    
    def test_overflow_write(self) -> None:
        self._pbb.append(b'Ruby Rose!')

        self._pbb.append(b'Yang')

        with open(self._pbb.filepath, 'rb') as f:
            self.assertSequenceEqual(f.read(), b'Ruby')
    
    def test_super_overflow_write(self) -> None:
        self._pbb.append(b'Ruby Rose!')

        self._pbb.append(b'Yang Xiao Long')

        with open(self._pbb.filepath, 'rb') as f:
            self.assertSequenceEqual(f.read(), b'Ruby Rose!Yang')

 
if __name__ == '__main__':
    unittest.main()