import sys, time, typing
from app.byte_buffer import ByteBuffer
from app.radio_stream import RadioStream
import logging

log = logging.getLogger('RadioRec')
log.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.DEBUG)

log.addHandler(consoleHandler)

def go() -> None:
    log.info('Creating stream one')
    streamOne = RadioStream(daemon=True)
    log.info('Stream one created')
    log.info(f"Stream one URL: {streamOne.url}")
    streamOne.start()
    log.info('Started stream one')

    # Introduce a de-sync
    log.info('Waiting 10 seconds...')
    time.sleep(10)
    log.info('Done waiting 10 seconds...')

    log.info('Creating stream two')
    streamTwo = RadioStream(daemon=True)
    log.info('Stream two created')
    log.info(f"Stream two URL: {streamTwo.url}")
    streamTwo.start()
    log.info('Started stream two')

    # Skip the pre-roll ad
    log.info('Waiting 45 seconds...')
    time.sleep(45)
    log.info('Done waiting 45 seconds...')

    # Pre-sync
    log.info('Reading stream 1')
    s1res = streamOne.byte_buffer.read(consume=False)
    log.info('Done reading stream 1')
    with open('./misc/output/s1rec-pre.aac', 'wb') as f:
        log.info('Writing pre-sync stream 1')
        f.write(s1res)
        log.info('Done pre-sync writing stream 1')

    log.info('Reading stream 2')
    s2res = streamTwo.byte_buffer.read(consume=False)
    log.info('Done reading stream 2')
    with open('./misc/output/s2rec-pre.aac', 'wb') as f:
        log.info('Writing pre-sync stream 2')
        f.write(s2res)
        log.info('Done pre-sync writing stream 2')

    syncBytes = streamOne.byte_buffer.readFromEnd(50000, consume=False)
    syncBytes = syncBytes[:47000]
    log.info('Seeking to sync bytes on stream two...')
    streamTwo.byte_buffer.seekToSequence(syncBytes)
    log.info('Seeking to sync bytes on stream one...')
    streamOne.byte_buffer.seekToSequence(syncBytes)

    # Post-sync
    log.info('Reading stream 1')
    s1res = streamOne.byte_buffer.read(consume=False)
    log.info('Done reading stream 1')
    with open('./misc/output/s1rec-post.aac', 'wb') as f:
        log.info('Writing post-sync stream 1')
        f.write(s1res)
        log.info('Done post-sync writing stream 1')

    log.info('Reading stream 2')
    s2res = streamTwo.byte_buffer.read(consume=False)
    log.info('Done reading stream 2')
    with open('./misc/output/s2rec-post.aac', 'wb') as f:
        log.info('Writing post-sync stream 2')
        f.write(s2res)
        log.info('Done post-sync writing stream 2')
    
    log.info('Waiting 90 seconds...')
    time.sleep(90)
    log.info('Done waiting 90 seconds...')

    # Post-wait
    log.info('Reading stream 1')
    s1res = streamOne.byte_buffer.read()
    log.info('Done reading stream 1')
    log.info('Reading stream 2')
    s2res = streamTwo.byte_buffer.read()
    log.info('Done reading stream 2')

    with open('./misc/output/s1rec-pw.aac', 'wb') as f:
        log.info('Writing post-wait stream 1')
        f.write(s1res)
        log.info('Done writing post-wait stream 1')

    with open('./misc/output/s2rec-pw.aac', 'wb') as f:
        log.info('Writing post-wait stream 2')
        f.write(s2res)
        log.info('Done writing post-wait stream 2')
    
    log.info('Done!')


go()