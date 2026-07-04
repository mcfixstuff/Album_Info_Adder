"""
utils.py

Helper functions for vinyl_metadata_helper.

Keeps parsing + tagging logic clean and reusable.
"""

import re
from pathlib import Path


def natural_sort_key(text):
    """
    Sort strings like:
        Track 1, Track 2, Track 10
    correctly instead of alphabetical order.
    """

    return [
        int(chunk) if chunk.isdigit() else chunk.lower()
        for chunk in re.split(r"(\d+)", text)
    ]


def get_opus_files(folder):
    """
    Returns sorted .opus files from a folder.
    Uses natural sort to ensure correct track order.
    """

    files = list(Path(folder).glob("*.opus"))

    files.sort(key=lambda x: natural_sort_key(x.name))

    return files


def clean_text(text):
    """
    Basic cleanup for Discogs parsing.
    """

    text = text.replace("—", "-")
    text = text.replace("–", "-")
    text = re.sub(r"\s+", " ", text).strip()

    return text


def strip_duration(title):
    """
    Removes trailing durations like:
        "Song Name 3:45"
    """

    return re.sub(r"\s+\d+:\d+$", "", title).strip()


def is_stop_section(line):
    """
    Detects Discogs sections where track parsing should stop.
    """

    stop_sections = {
        "credits",
        "companies",
        "notes",
        "barcode",
        "barcodes",
        "matrix",
        "identifiers",
        "recommendations",
        "master release",
        "versions",
        "more images"
    }

    return line.lower().strip() in stop_sections


def split_artist_title(line):
    """
    Splits:
        Artist - Title
        Artist – Title

    Returns (artist, title) or None
    """

    if "–" in line:
        parts = line.split("–", 1)
    elif "-" in line:
        parts = line.split("-", 1)
    else:
        return None

    artist = clean_text(parts[0])
    title = clean_text(parts[1])

    artist = artist.rstrip("*")

    return artist, title


def extract_year(lines):
    """
    Finds year from Discogs text.
    """

    for i, line in enumerate(lines):
        if line.lower().strip() == "year:":
            if i + 1 < len(lines):
                return clean_text(lines[i + 1])

    return ""