import sys, time, typing
from app.byte_buffer import ByteBuffer
from app.radio_stream import RadioStream
import logging

log = logging.getLogger('RadioRec')
log.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.DEBUG)

log.addHandler(consoleHandler)

def go() -> None:
    log.debug('Creating stream one')
    streamOne = RadioStream()
    log.debug('Stream one created')
    streamOne.start()
    log.debug('Started stream one')

    # Introduce a de-sync
    log.debug('Waiting 10 seconds...')
    time.sleep(10)
    log.debug('Done waiting 10 seconds...')

    log.debug('Creating stream two')
    streamTwo = RadioStream()
    log.debug('Stream two created')
    streamTwo.start()
    log.debug('Started stream two')

    # Skip the pre-roll ad
    log.debug('Waiting 20 seconds...')
    time.sleep(20)
    log.debug('Done waiting 20 seconds...')

    # Dump everything recorded thus far
    streamOne.byte_buffer.seekToEnd()
    streamTwo.byte_buffer.seekToEnd()
    log.debug('Seeked to end of both streams')

    log.debug('Waiting 15 seconds...')
    time.sleep(15)
    log.debug('Done waiting 15 seconds...')

    syncBytes = streamOne.byte_buffer.readFromEnd(1000, consume=False)
    try:
        log.debug('Seeking to sync bytes on stream two...')
        streamTwo.byte_buffer.seekToSequence(syncBytes)
        log.debug('Seeking to sync bytes on stream one...')
        streamOne.byte_buffer.seekToSequence(syncBytes)
    except ValueError:
        print("Whoops!")
    
    log.debug('Waiting 10 seconds...')
    time.sleep(10)
    log.debug('Done waiting 10 seconds...')

    log.debug('Reading stream 1')
    s1res = streamOne.byte_buffer.read()
    log.debug('Done reading stream 1')
    with open('./misc/output/s1rec.aac', 'wb') as f:
        log.debug('Writing stream 1')
        f.write(s1res)
        log.debug('Done writing stream 1')

    log.debug('Reading stream 2')
    s2res = streamTwo.byte_buffer.read()
    log.debug('Done reading stream 2')
    with open('./misc/output/s2rec.aac', 'wb') as f:
        log.debug('Writing stream 2')
        f.write(s2res)
        log.debug('Done writing stream 2')
    
    log.debug('Done!')


go()