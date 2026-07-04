# Album Info Adder

Album Info Adder is a small desktop tool for tagging Opus audio files with metadata pulled from Discogs-style text.

## What it does

The project includes two main tools:

1. Main program
   - Paste Discogs text into the GUI
   - Choose a folder of .opus files
   - Preview how each file will be tagged
   - Apply metadata and rename the files to the format `01 Track Name.opus`

2. Metadata editor
   - Open a folder of .opus files
   - View and edit metadata fields such as title, artist, album artist, album, date, track number, and genre
   - Save the changes directly to the files

## Requirements

Install the Python dependency:

```bash
python -m pip install mutagen
```

## Run the main program

```bash
python main.py
```

## Run the metadata editor

```bash
python metadata_editor.py
```

## How the main workflow works

1. Paste Discogs text into the text box.
2. Choose a folder containing .opus files.
3. Click Preview to see the parsed track list.
4. Optionally enter a year override in the Year field.
5. Click Apply tags to write metadata and rename the files.

## Notes

- The app writes the track title, track number, and date into the Opus metadata.
- For compilations, it writes the track artist separately and uses `Various Artists` for the album artist field.
- Files are renamed to include the track number and title.
