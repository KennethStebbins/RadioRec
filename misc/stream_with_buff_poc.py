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
    startingTime = time.time()
    streamOne = RadioStream(daemon=True)
    endingTime = time.time()
    log.debug(f'Stream one created. Took {endingTime-startingTime} seconds.')
    streamOne.start()
    log.debug('Started stream one')

    # Introduce a de-sync
    log.debug('Waiting 10 seconds...')
    time.sleep(10)
    log.debug('Done waiting 10 seconds...')

    log.debug('Creating stream two')
    streamTwo = RadioStream(daemon=True)
    log.debug('Stream two created')
    streamTwo.start()
    log.debug('Started stream two')

    # Skip the pre-roll ad
    log.debug('Waiting 45 seconds...')
    time.sleep(45)
    log.debug('Done waiting 45 seconds...')

    syncBytes = streamOne.byte_buffer.readFromEnd(50000, consume=False)
    syncBytes = syncBytes[:47000]
    log.debug('Seeking to sync bytes on stream two...')
    streamTwo.byte_buffer.seekToSequence(syncBytes)
    log.debug('Seeking to sync bytes on stream one...')
    streamOne.byte_buffer.seekToSequence(syncBytes)
    
    log.debug('Waiting 90 seconds...')
    time.sleep(90)
    log.debug('Done waiting 90 seconds...')

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