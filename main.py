import argparse, logging, os, sys
from datetime import datetime, timedelta
from threading import Event

from app.radio_stream import PersistentRedundantRadioStream
from app.byte_buffer import ByteBuffer, PersistentByteBuffer

DATETIME_PARSE_FORMAT : str = r'%Y-%m-%d %H:%M:%S'
DATETIME_FILE_FORMAT : str = r'%Y-%m-%d_%H%M'

log = logging.getLogger('RadioRec')

def _prepLogger(filepath : str = None) -> logging.Logger:
    
    class HiLoFilter(logging.Filter):
        _low : int = None
        _high : int = None

        def __init__(self, low : int = logging.DEBUG, 
                high : int = logging.CRITICAL) -> None:
            self._low = low
            self._high = high

            super().__init__()
        
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno >= self._low \
                and record.levelno <= self._high

    log = logging.getLogger('RadioRec')

    # Clean out all previously-added handlers
    [log.removeHandler(f) for f in log.handlers]

    stdoutHandler = logging.StreamHandler(sys.stdout)
    stdoutHandler.setLevel(logging.DEBUG)
    stdoutHandler.addFilter(HiLoFilter(high=logging.INFO))
    log.addHandler(stdoutHandler)

    stderrHandler = logging.StreamHandler(sys.stderr)
    stderrHandler.setLevel(logging.WARNING)
    log.addHandler(stderrHandler)

    if filepath is not None:
        fileHandler = logging.FileHandler(filepath, 'a')
        fileHandler.setLevel(logging.DEBUG)
        log.addHandler(fileHandler)

    return log

def _parseArgs() -> argparse.Namespace:
    ap = argparse.ArgumentParser()

    ap.add_argument('-u', '--url', required=True,
        help="Stream URL to record")
    ap.add_argument('-o', '--output-dir', required=True,
        help="Directory where recorded files should be placed")
    
    ap.add_argument('-s', '--start-date', default=None,
        help="Date on which to start the recording. Format: yyyy-mm-dd HH:MM:SS")
    ap.add_argument('-e', '--end-date', default=None,
        help="Date on which to end the recording. Format: yyyy-mm-dd HH:MM:SS")
    
    ap.add_argument('-v', '--verbose', action='store_true',
        help="Turn on more verbose logging")
    ap.add_argument('--log-file', default=None,
        help="Save all logs to this file")
    
    ap.add_argument('--redundancy', type=int, default=2,
        help="The number of backup streams to run")
    ap.add_argument('--overwrite', action='store_true',
        help="If specified, the program won't hesitate before " + 
            "overwriting existing audio files in the output directory")
    
    return ap.parse_args()


def wait_until(date : datetime) -> None:
    e = Event()

    now = datetime.now()
    if date < now:
        return
    
    longTimedelta = timedelta(seconds=15)
    # Check the current date less often when we're
    # very far out from the target date
    while date - datetime.now() > longTimedelta:
        e.wait(10)
    
    shortTimedelta = timedelta(seconds=1)
    while date - datetime.now() > shortTimedelta:
        e.wait(0.1)
    
    while date > datetime.now():
        e.wait(0.01)

def record_until(prrs : PersistentRedundantRadioStream,
        output_dir : str, endDate : datetime) -> str:
    now = datetime.now()
    fileName = f"{now.strftime(DATETIME_FILE_FORMAT)}.aac"
    filePath = os.path.join(output_dir, fileName)

    prrs.filepath = filePath
    prrs.should_write = True

    wait_until(endDate)

def record_hour(prrs : PersistentRedundantRadioStream, 
        output_dir : str) -> str:
    endDate = datetime.now() + timedelta(hours=1)
    endDate = endDate.replace(minute=0, second=0, microsecond=0)

    record_until(prrs, output_dir, endDate)

def main() -> None:
    args = _parseArgs()

    log = _prepLogger(args.log_file)

    if args.verbose:
        log.setLevel(logging.DEBUG)
        log.debug("Verbose logging enabled")

    if args.start_date:
        try:
            startDate = datetime.strptime(args.start_date, DATETIME_PARSE_FORMAT)
        except ValueError as e:
            log.critical(f"Failed to parse start date: {args.start_date}")
            raise ValueError("Unable to parse given start date") from e

    if args.end_date:
        try:
            endDate = datetime.strptime(args.end_date, DATETIME_PARSE_FORMAT)
            endHour = endDate.replace(minute=0, second=0, microsecond=0)
        except ValueError as e:
            log.critical(f"Failed to parse end date: {args.end_date}")
            raise ValueError("Unable to parse given end date") from e

    outputFilePath = os.path.join(args.output_dir, 'output.aac')
    try:
        log.debug("About to instantiate PRRS...")

        prrs = PersistentRedundantRadioStream(outputFilePath, args.url,
                redundancy=args.redundancy, overwrite=args.overwrite,
                should_write=False)
    except FileExistsError:
        pass

    log.debug("PRRS instantiated.")

    log.debug("Starting PRRS...")
    prrs.start()
    log.debug("PRRS started")

    if args.start_date:
        wait_until(startDate)
        prrs.byte_buffer.seekToEnd()

    try:
        while not args.end_date or endHour > datetime.now():
            record_hour(prrs, args.output_dir)
        
        if args.end_date and endDate > endHour:
            record_until(prrs, args.output_dir, endDate)
    except KeyboardInterrupt:
        log.info("Stopping...")
    finally:
        prrs.writeAll()
        prrs.should_write = False
    

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass