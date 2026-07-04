"""
tagger.py

Writes metadata to .opus files.

Only updates:
    TITLE
    TRACKNUMBER
    DATE
    ARTIST (only for Various Artists albums)

Everything else is left untouched.
"""

import os
import re
import sys
from pathlib import Path

try:
    import mutagen
    from mutagen import File as MutagenFile
except ModuleNotFoundError:  # pragma: no cover - exercised when dependency is missing
    mutagen = None
    MutagenFile = None


def _require_mutagen():
    if mutagen is None or MutagenFile is None:
        python_path = sys.executable or os.sys.executable
        raise ModuleNotFoundError(
            "mutagen is required to write audio tags. "
            f"This app is running with: {python_path}. "
            "Install it into that interpreter with: python -m pip install mutagen"
        )
    return MutagenFile


def sanitize_filename_part(value):
    """Create a filesystem-safe filename segment from a track title."""

    value = re.sub(r"[\\/:*?\"<>|]", "", value or "")
    value = re.sub(r"\s+", " ", value).strip()
    return value or "track"


def build_target_filename(index, track, suffix=".opus"):
    """Create a target filename like 01 Track Name.opus."""

    title = sanitize_filename_part(track.get("title", ""))
    return f"{index:02d} {title}{suffix}"


def get_audio_files(folder):
    """
    Returns a naturally sorted list of audio files that mutagen can read.
    """

    files = []
    for path in Path(folder).iterdir():
        if not path.is_file():
            continue

        try:
            if MutagenFile(path):
                files.append(path)
        except Exception:
            continue

    def sort_key(path):
        import re

        numbers = re.findall(r"\d+", path.name)

        if numbers:
            return int(numbers[0])

        return 999999

    files.sort(key=sort_key)

    return files


def write_tags(folder, album_data):
    """
    Writes metadata to every supported audio file.

    album_data should come directly from parser.py
    """

    files = get_audio_files(folder)
    tracks = album_data["tracks"]

    if len(files) != len(tracks):
        raise ValueError(
            f"Found {len(files)} supported audio files but parsed {len(tracks)} tracks."
        )

    mutagen_file = _require_mutagen()

    for index, (file, track) in enumerate(zip(files, tracks), start=1):

        audio = mutagen_file(file)

        #
        # Always overwrite these
        #

        audio["TITLE"] = [track["title"]]
        audio["TRACKNUMBER"] = [str(index)]
        audio["DATE"] = [album_data["year"]]

        #
        # Track artist and album artist
        #

        if album_data["various"]:
            audio["ARTIST"] = [track["artist"]]
            audio["ALBUMARTIST"] = ["Various Artists"]
        else:
            audio["ARTIST"] = [album_data["album_artist"]]
            audio.pop("ALBUMARTIST", None)

        audio.save()

    return len(files)


def rename_files(folder, album_data):
    """Rename each supported audio file to match the track number and title."""

    files = get_audio_files(folder)
    tracks = album_data["tracks"]

    if len(files) != len(tracks):
        raise ValueError(
            f"Found {len(files)} supported audio files but parsed {len(tracks)} tracks."
        )

    for index, (file, track) in enumerate(zip(files, tracks), start=1):
        suffix = file.suffix
        target_name = build_target_filename(index, track, suffix)
        target_path = file.with_name(target_name)

        if file != target_path:
            if target_path.exists():
                raise FileExistsError(f"Destination file already exists: {target_path.name}")
            file.rename(target_path)

    return len(files)


def preview(folder, album_data):
    """
    Returns a list that the GUI can display.

    [
        {
            "file": "...",
            "title": "...",
            "artist": "...",
            "track": 1
        }
    ]
    """

    files = get_audio_files(folder)

    if len(files) != len(album_data["tracks"]):
        raise ValueError(
            f"Found {len(files)} supported audio files but parsed {len(album_data['tracks'])} tracks."
        )

    preview_rows = []

    for number, (file, track) in enumerate(zip(files, album_data["tracks"]), start=1):

        preview_rows.append({
            "file": file.name,
            "title": track["title"],
            "artist": track["artist"] if album_data["various"] else "(unchanged)",
            "track": number
        })

    return preview_rows


#
# Standalone testing
#

if __name__ == "__main__":

    sample = {
        "album": "Orleans",
        "album_artist": "Orleans",
        "year": "1973",
        "various": False,
        "tracks": [
            {
                "artist": "Orleans",
                "title": "Please Be There"
            },
            {
                "artist": "Orleans",
                "title": "If"
            }
        ]
    }

    folder = input("Folder containing .opus files: ").strip()

    print("\nPreview:\n")

    rows = preview(folder, sample)

    for row in rows:
        print(row)

    answer = input("\nWrite tags? (y/n): ").lower()

    if answer == "y":
        count = write_tags(folder, sample)
        print(f"\nDone! Updated {count} files.")