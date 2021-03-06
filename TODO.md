- [ ] Write unit tests:
    - [ ] ...for URL parameters in all the different RadioStream-related classes
    - [ ] ...for changing the filepath of a PBB after it has been created
    - [ ] ...for passthrough filepath properties on PRRS
    - [ ] ...for RSM failing over to the longest stream.
    - [ ] ...for starting and stopping recording on PersistentByteBuffer
    - [ ] ...for starting and stopping recording on PRRS
    - [ ] ...for writing everything to disk on PersistentByteBuffer
    - [ ] ...for writing everything to disk on PRRS
    - [ ] ...for redundant_max_age_sec parameter in RSM, RRS, and PRRS
    - [ ] ...for start_date in RadioStream
    - [ ] ...for redundant_max_age_sec in RSM when redundancy < 2
- [ ] ? Give PersistentRedundantRadioStream a better name.
- [ ] Clean up and better standardize tests
    - Make sure all test functions are annotated as returning None
    - Combine related tests in test_byte_buffer into a class, instead of giving each case its own class
- [ ] Clean up and better standardize quote usage
- [ ] Document!!
- [x] Build CLI
- [x] Build in functionality to the PersistentByteBuffer and PRRS to start and stop writing data to disk.
- [x] Build in functionality to PersistentByteBuffer and PRRS to dump everything to disk
- [x] Modify RadioStreamManager to select the stream with the largest buffer when failing over
- [x] Add locks back to helper methods in ByteBuffer
- [x] Write unit tests for new ByteBuffer functionality
- [x] Refactor ByteBuffer to use private variables properly and expose some as properties
    - Things that should be properties:
        - `byte_array` (ro)
        - `length` (ro)
        - `readable_length` (ro)
- [x] Finish syncing mechanic in Redundant Radio Stream
- [x] Refactor ByteBuffer to have the proper prefix on private methods (one `_` instead of two `__`)
- [x] Write unit tests for new RadioStream and RadioStream-related functionality
- [x] Write PersistentByteBuffer that writes data on append
- [x] Modify RedundantRadioStream to allow you to give them byte buffers on init
- [x] Use setUpClass() and rearrange tests in test_radio_stream to better separate the properties and methods tested within a test case, instead of lumping it all together into one method.