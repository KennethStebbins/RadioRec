from typing import Callable
from app.radio_stream import RadioStream, RadioStreamManager, RedundantRadioStream
from threading import Event
from unittest import TestCase, main as start_test
from unittest.loader import TestLoader
from unittest.suite import TestSuite

class TestRadioStreamCreation(TestCase):
    _dummyURL : str = "https://kennethstebbins.com"

    def test_init(self):
        rs = RadioStream()

        self.assertIsInstance(rs, RadioStream)
        self.assertIsNotNone(rs._url)
    
    def test_url(self):
        expected = self._dummyURL

        rs = RadioStream(url=expected)

        self.assertIsInstance(rs, RadioStream)
        self.assertEqual(rs._url, expected)

    def test_buffer_size(self):
        expected = 1000

        rs = RadioStream(buffer_size=expected, url=self._dummyURL)

        self.assertIsInstance(rs, RadioStream)
        self.assertEqual(rs._byte_buffer.length, expected)

    def test_preroll_len(self):
        expected = 1000

        rs = RadioStream(preroll_len=expected, url=self._dummyURL)

        self.assertIsInstance(rs, RadioStream)
        self.assertEqual(rs._preroll_len, expected)

class TestRadioStreamProperties(TestCase):
    _dummyURL : str = "https://kennethstebbins.com"
    _rs : RadioStream = None

    def setUp(self) -> None:
        self._rs = RadioStream(url=self._dummyURL)
    
    def test_byte_buffer(self):
        self.assertEqual(self._rs.byte_buffer, self._rs._byte_buffer)
    
    def test_url(self):
        self.assertEqual(self._rs.url, self._rs._url)

class TestRadioStreamStartAndStop(TestCase):
    _rs : RadioStream = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._rs = RadioStream()

    def test_0_start(self):
        e = Event()

        self._rs.start()
        
        e.wait(17)

        firstLen = self._rs.byte_buffer.readable_length
        self.assertGreater(firstLen, 0)

        e.wait(1)

        secondLen = self._rs.byte_buffer.readable_length
        self.assertGreater(secondLen, firstLen)
    
    def test_1_stop(self):
        e = Event()

        self._rs.stop()

        e.wait(1)

        self.assertFalse(self._rs.is_alive())

class TestRadioStreamManagerCreation(TestCase):
    def test_init(self):
        rsm = RadioStreamManager()

        self.assertIsInstance(rsm, RadioStreamManager)

    def test_redundancy(self):
        expected = 5

        rsm = RadioStreamManager(redundancy=expected)

        self.assertIsInstance(rsm, RadioStreamManager)
        self.assertEqual(rsm._desired_redundancy, expected)

    def test_zero_redundancy(self):
        with self.assertRaises(ValueError) as cm:
            RadioStreamManager(redundancy=0)

        self.assertEqual(cm.exception.args[0], 
            'Cannot have a redundancy less than 1')

    def test_buffer_size(self):
        expected = 1000

        rsm = RadioStreamManager(buffer_size=expected)

        self.assertIsInstance(rsm, RadioStreamManager)
        self.assertEqual(rsm._desired_buffer_size, expected)

    def test_start_attempts(self):
        expected = 5

        rsm = RadioStreamManager(start_attempts=expected)

        self.assertIsInstance(rsm, RadioStreamManager)
        self.assertEqual(rsm._stream_start_attempts, expected)

    def test_on_stream_failover(self):
        def handle_failover(old : RadioStream, new : RadioStream) -> None:
            self.fail("This handler should not have been called")
        
        rsm = RadioStreamManager(on_stream_failover=handle_failover)

        self.assertIn(handle_failover, rsm._stream_failover_handlers)
    
    def test_on_stream_failover_followup(self):
        expected = 0

        rsm = RadioStreamManager()

        self.assertEqual(len(rsm._stream_failover_handlers), expected)

class TestRadioStreamManagerFailoverHandlers(TestCase):
    _rsm : RadioStreamManager = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._rsm = RadioStreamManager()

    def _handle_failover(self, old : RadioStream, new : RadioStream) -> None:
        self.fail("This handler should not have been called")

    def test_0_add_remove_handler(self):
        rsm = self._rsm

        ## Add
        rsm.add_stream_failover_handler(self._handle_failover)

        self.assertIn(self._handle_failover, rsm._stream_failover_handlers)
        self.assertEqual(len(rsm._stream_failover_handlers), 1)

        ## Remove
        rsm.remove_stream_failover_handler(self._handle_failover)

        self.assertEqual(len(rsm._stream_failover_handlers), 0)

class TestRadioStreamManagerStartAndFailover(TestCase):
    _rsm : RadioStreamManager = None
    _redundancy : int = 2

    @classmethod
    def setUpClass(cls) -> None:
        cls._rsm = RadioStreamManager(redundancy=cls._redundancy)

    def test_0_start(self):
        rsm = self._rsm
        e = Event()

        rsm.start()

        e.wait(90)

        self.assertIsInstance(rsm._primary_radio_stream, RadioStream)
        self.assertEqual(len(rsm._redundant_radio_streams), self._redundancy)
        for stream in rsm._redundant_radio_streams:
            self.assertIsInstance(stream, RadioStream)

    def test_1_prs_property(self) -> None:
        rsm = self._rsm

        self.assertEqual(rsm.primary_radio_stream, rsm._primary_radio_stream)    
    
    def test_2_restore_redundancy(self) -> None:
        rsm = self._rsm
        e = Event()

        oldStream = rsm._redundant_radio_streams[0]
        oldStream.stop()

        e.wait(15)

        self.assertEqual(len(rsm._redundant_radio_streams), self._redundancy)
        for stream in rsm._redundant_radio_streams:
            self.assertNotEqual(stream, oldStream)

    def test_3_primary_stream_failover(self) -> None:
        rsm = self._rsm
        e = Event()
        oldPRS : RadioStream = rsm.primary_radio_stream

        def handle_failover(old : RadioStream, new : RadioStream) -> None:
            self.assertEqual(old, oldPRS)
            self.assertFalse(old.is_alive())
            self.assertIsInstance(new, RadioStream)
            self.assertNotEqual(old, new)

            e.set()

        rsm.add_stream_failover_handler(handle_failover)

        oldPRS.stop()

        e.wait(60)
        rsm.remove_stream_failover_handler(handle_failover)

        self.assertTrue(e.is_set())

    def test_4_complete_failure(self) -> None:
        rsm = self._rsm
        e = Event()

        with rsm._radio_stream_lock:
            oldStreams = list(rsm._redundant_radio_streams)
            oldStreams += [rsm.primary_radio_stream]

            for stream in oldStreams:
                stream.stop()
            
        e.wait(90)

        self.assertIsNotNone(rsm.primary_radio_stream)
        self.assertEqual(len(rsm._redundant_radio_streams), self._redundancy)
        self.assertNotIn(rsm.primary_radio_stream, oldStreams)
        for stream in rsm._redundant_radio_streams:
            self.assertNotIn(stream, oldStreams)

class TestRedundantRadioStreamCreationAndProperties(TestCase):
    def test_init(self) -> None:
        rrs = RedundantRadioStream()

        self.assertIsInstance(rrs, RedundantRadioStream)
        self.assertIsInstance(rrs._radio_stream_manager, RadioStreamManager)
        self.assertIn(rrs.handleFailover, 
            rrs._radio_stream_manager._stream_failover_handlers)
    
    def test_init_redundancy(self) -> None:
        expected = 5

        rrs = RedundantRadioStream(redundancy=expected)

        self.assertEqual(rrs._radio_stream_manager._desired_redundancy, expected)
    
    def test_init_buffer_size(self) -> None:
        expected = 38271

        rrs = RedundantRadioStream(buffer_size=expected)

        self.assertEqual(rrs._radio_stream_manager._desired_buffer_size, expected)
        self.assertEqual(rrs._byte_buffer.length, expected)
    
    def test_init_start_attempts(self) -> None:
        expected = 5

        rrs = RedundantRadioStream(start_attempts=expected)

        self.assertEqual(rrs._radio_stream_manager._stream_start_attempts, expected)
    
    def test_init_sync_len(self) -> None:
        expected = 3824

        rrs = RedundantRadioStream(sync_len=expected)

        self.assertEqual(rrs._sync_len, expected)
    
    def test_property_byte_buffer(self) -> None:
        rrs = RedundantRadioStream()

        self.assertEqual(rrs._byte_buffer, rrs.byte_buffer)

class TestRedundantRadioStreamFunctions(TestCase):
    _rrs : RedundantRadioStream = None

    @classmethod
    def setUpClass(cls) -> None:
        cls._rrs = RedundantRadioStream()

    def test_0_start(self) -> None:
        rrs = self._rrs
        e = Event()

        rrs.start()

        e.wait(80)

        self.assertGreater(rrs.byte_buffer.readable_length, 0)
        oldReadableLen = rrs.byte_buffer.readable_length

        e.wait(5)

        self.assertGreater(rrs.byte_buffer.readable_length, oldReadableLen)

    def test_1_failover(self) -> None:
        rrs = self._rrs
        rsm = rrs._radio_stream_manager
        oldPRS = rsm.primary_radio_stream
        e = Event()

        reference = RadioStream()
        reference.start()

        e.wait(30)

        testBytes = rrs.byte_buffer.readFromEnd(70000, consume=False)[0:50000]

        try:
            reference.byte_buffer.seekToSequence(testBytes)
            refBytes = reference.byte_buffer.read()
        except ValueError as ex:
            raise RuntimeError("Could not find bytes from the old PRS in " + 
                "the reference stream") from ex

        oldPRS.stop()

        e.wait(20)

        newPRS = rsm.primary_radio_stream
        self.assertNotEqual(oldPRS, newPRS)

        refBytes += reference.byte_buffer.readUpToRemainingLength(10000)

        try:
            rrs.byte_buffer._findSequence(refBytes)
        except ValueError as ex:
            print(ex)
            self.fail("Could not find reference bytes in redundant radio " + 
                "stream's byte buffer")



# def load_tests(loader : TestLoader, tests, pattern) -> TestSuite:
#     suite = TestSuite()

#     tests = loader.loadTestsFromTestCase(TestRedundantRadioStreamCreationAndProperties)
#     suite.addTests(tests)

#     tests = loader.loadTestsFromTestCase(TestRedundantRadioStreamFunctions)
#     suite.addTests(tests)

#     return suite

if __name__ == '__main__':
    start_test()