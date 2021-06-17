# 3.2.0
- Refactored code
- Remove diarization and punctuation that has been moved upward server-side. 
- Added model loading time logging
- Refactored logging
- Added overload for all environment parameter as launch arguments.
- Removed file writing on disk to speed processing time.
- Refactored error handling, logs and error messages

# 3.1.1
- Change Pykaldi with vosk-API (no python wrapper for decoding function, no extrat packages during installation, c++ implementation based on kaldi functions)
- New feature: Compute a confidence score per transcription
- Fix minor bugs

# 2.2.1
- Fix minor bugs
- put SWAGGER_PATH parameter as optional
- Generate the word_boundary file if it does not exist

# 2.2.0
- Speaker diarization feature: pyBK package
- Mulithreading feature: Speech decoding and Speaker diarization processes
- Optional parameter: real number of speaker in the audio

# 2.0.0
- Reimplement LinTO-Platform-stt-standalone-worker using Pykaldi package

# 1.1.2
- New features:
    - Word timestamp computing
    - Response type: plain/text: simple text output and application/json: the transcription and the words timestamp.
    - Swagger: integrate swagger in the service using a python package
    - Fix minor bugs

# 1.0.0
- First build of LinTO-Platform-stt-standalone-worker