# SQ Decoder Application

## Installation

1. Ensure you have Python 3.12 installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Program

1. Run the main script:
   ```bash
   python main.py
   ```
2. Use the GUI to open a stereo CBS SQ encoded WAV file and select an output FLAC file location.
3. Click "Decode" to start the decoding process.

## Current Decoder Limitations

- The current decoder uses a basic fixed-matrix implementation of the CBS SQ decoding matrix.
- There is no advanced logic-steering decoding implemented yet.

## Future Improvements

- Implement a more accurate SQ decoding algorithm based on published CBS SQ specifications.
- Add support for different input formats and sample rates with proper error handling.
- Enhance the user interface with additional features like batch processing or logging.