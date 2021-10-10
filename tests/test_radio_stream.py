import unittest
from app.radio_stream import RadioStream, RadioStreamManager, RedundantRadioStream
from threading import Event
from unittest import TestCase, main as start_test

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

    def setUp(self) -> None:
        self._rs = RadioStream()

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

        self.assertFalse(self._rs.is_alive)

class TestRadioStreamManagerCreation(TestCase):
    def test_init(self):
        rsm = RadioStreamManager()

        self.assertIsInstance(rsm, RadioStreamManager)

    def test_redundancy(self):
        expected = 5

        rsm = RadioStreamManager(redundancy=expected)

        self.assertIsInstance(rsm, RadioStreamManager)
        self.assertEqual(rsm._desired_redundancy, expected)

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

    def test_sync_seq_length(self):
        expected = 2000

        rsm = RadioStreamManager(sync_seq_length=expected)

        self.assertIsInstance(rsm, RadioStreamManager)
        self.assertEqual(rsm._sync_seq_length, expected)

    def test_on_stream_failover(self):
        def handle_failover(old : RadioStream, new : RadioStream) -> None:
            self.fail("This handler should not have been called")
        
        rsm = RadioStreamManager(on_stream_failover=handle_failover)

        self.assertIn(handle_failover, rsm._stream_failover_handlers)

class TestRadioStreamManagerFailoverHandlers(TestCase):
    _rsm : RadioStreamManager = None

    def setUp(self) -> None:
        self._rsm = RadioStreamManager()
    
    def _handle_failover(self, old : RadioStream, new : RadioStream) -> None:
        self.fail("This handler should not have been called")

    def test_0_add_handler(self):
        self._rsm.add_stream_failover_handler(self._handle_failover)

        self.assertIn(self._handle_failover, self._rsm._stream_failover_handlers)

    def test_1_remove_handler(self):
        self.assertIn(self._handle_failover, self._rsm._stream_failover_handlers)

        self._rsm.remove_stream_failover_handler(self._handle_failover)

        self.assertEqual(len(self._rsm._stream_failover_handlers), 0)

class TestRadioStreamManagerStartAndFailover(TestCase):
    _rsm : RadioStreamManager = None
    _redundancy : int = 2

    def setUp(self) -> None:
        self._rsm = RadioStreamManager(redundancy=self._redundancy)

    def test_0_start(self):
        rsm = self._rsm
        e = Event()

        self._rsm.start()

        e.wait(35)

        self.assertIsInstance(rsm._primary_radio_stream, RadioStream)
        self.assertEqual(len(rsm._redundant_radio_streams), self._redundancy)
        for stream in rsm._redundant_radio_streams:
            self.assertIsInstance(stream, RadioStream)

    def test_1_prs_property(self):
        self.assertIsNotNone(self._rsm._primary_radio_stream)
        self.assertEqual(self._rsm.primary_radio_stream, self._rsm._primary_radio_stream)    
    
    def test_2_restore_redundancy(self):
        rsm = self._rsm
        e = Event()

        oldStream = rsm._redundant_radio_streams[0]
        oldStream.stop()

        e.wait(15)

        self.assertEqual(len(rsm._redundant_radio_streams), self._redundancy)
        for stream in rsm._redundant_radio_streams:
            self.assertNotEqual(stream, oldStream)

    def test_3_failover_from_redundants(self):
        rsm = self._rsm
        e = Event()

        oldPRS : RadioStream = rsm.primary_radio_stream

        def handle_failover(old : RadioStream, new : RadioStream) -> None:
            self.assertEqual(old, oldPRS)
            self.assertFalse(old.is_alive)
            self.assertIsInstance(new, RadioStream)
            self.assertNotEqual(old, new)

            e.set()

        rsm.add_stream_failover_handler(handle_failover)

        oldPRS.stop()

        e.wait(60)
        rsm.remove_stream_failover_handler(handle_failover)

        self.assertTrue(e.is_set())

    def test_4_failover_all_dead(self):
        rsm = self._rsm
        e = Event()

        def handle_failover(old : RadioStream, new : RadioStream) -> None:
            e.set()

        rsm.add_stream_failover_handler(handle_failover)

        with rsm._radio_stream_lock:
            oldStreams = rsm._redundant_radio_streams
            oldStreams += [rsm.primary_radio_stream]

            for stream in oldStreams:
                stream.stop()
            
        e.wait(180)
        rsm.remove_stream_failover_handler(handle_failover)

        self.assertIsNotNone(rsm.primary_radio_stream)
        self.assertEqual(len(rsm._redundant_radio_streams), self._redundancy)
        self.assertNotIn(rsm.primary_radio_stream, oldStreams)
        for stream in rsm._redundant_radio_streams:
            self.assertNotIn(stream, oldStreams)
        

if __name__ == '__main__':
    start_test(failfast=True)