"""
parser.py

Parses copied Discogs text into structured album/track information.

Supported:
- Standard albums
- Various Artists compilations
- Multi-disc releases (1A, 2B, 4C, etc.)

Returns:

{
    "album": "...",
    "album_artist": "...",
    "year": "...",
    "various": True/False,
    "tracks": [
        {
            "artist": "...",
            "title": "..."
        }
    ]
}
"""

import re


STOP_SECTIONS = {
    "credits",
    "companies",
    "notes",
    "barcode",
    "barcodes",
    "matrix",
    "identifiers",
    "recommendations",
    "seller terms",
    "master release",
    "versions",
    "more images",
    "reviews"
}


def clean_line(line):
    """Normalize whitespace and strip common markdown noise."""
    line = line.strip()
    line = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", line)
    line = re.sub(r"^#+\s*", "", line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def looks_like_track_code(text):
    """
    Detect things like:
        A1
        B4
        1A
        7D
        AA1
    """

    return bool(re.match(r"^[A-Z]?\d+[A-Z]?$", text, re.I))


def split_various(line):
    """
    Split:

    Chic–Le Freak

    into

    ('Chic', 'Le Freak')
    """

    line = line.replace("—", "–")
    line = re.sub(r"\s+", " ", line).strip()

    if "–" not in line:
        return None

    artist, title = line.split("–", 1)

    artist = clean_line(artist).rstrip("*")
    title = clean_line(title)

    return artist, title


def remove_time(title):
    """
    Removes trailing runtimes.

    Example:
        Please Be There    3:48
        -> Please Be There
    """

    title = re.sub(r"\s+\d+:\d+$", "", title).strip()
    title = re.sub(r"\s+\d+\s*$", "", title).strip()
    return title


def looks_like_written_by(text):
    return bool(re.search(r"written-by", text, re.I))


def split_inline_tracks(text):
    """Split a line like 'Song 1 3:29Song 2 4:21' into title chunks."""

    text = text.strip()
    if not text:
        return []

    if re.search(r"\d{1,2}:\d{2}", text):
        chunks = []
        for match in re.finditer(r"(?P<title>.+?)(?P<runtime>\d{1,2}:\d{2})(?=(?:.+?\d{1,2}:\d{2})|$)", text):
            title = match.group("title").strip()
            if title:
                chunks.append(title)
        return chunks

    return [text]


def parse_discogs(text):

    lines = [clean_line(x) for x in text.splitlines()]
    lines = [x for x in lines if x]

    if not lines:
        raise ValueError("No Discogs text supplied.")

    album_artist = ""
    album = ""
    year = ""
    various = False

    tracks = []

    #
    # Album / Artist
    #

    for line in lines:
        if " – " in line and not line.lower().startswith(("label:", "format:", "country:", "released:", "genre:", "style:")):
            album_artist, album = line.split(" – ", 1)
            album_artist = album_artist.strip()
            album = album.strip()
            break

    if not album_artist and lines:
        first = lines[0]
        if " – " in first:
            album_artist, album = first.split(" – ", 1)
            album_artist = album_artist.strip()
            album = album.strip()

    #
    # Year
    #

    for i, line in enumerate(lines):
        lower = line.lower()
        if lower == "year:" or lower == "released:":
            if i + 1 < len(lines):
                candidate = lines[i + 1]
                if candidate.lower() not in {"released:", "genre:", "style:", "country:"}:
                    year = candidate
            break

    if not year:
        for line in lines:
            if re.match(r"^\d{4}$", line):
                year = line
                break

    various = album_artist.lower().startswith("various")

    #
    # Find beginning of track listing
    #

    start = None

    for i, line in enumerate(lines):
        lower = line.lower()
        if lower == "year:" or lower == "released:":
            start = i + 2
            break

    if start is None:
        raise ValueError("Couldn't find a usable track section.")

    #
    # Parse tracks
    #

    for line in lines[start:]:

        lower = line.lower()

        if lower in STOP_SECTIONS:
            break

        if lower.startswith("a") or lower.startswith("b") or re.match(r"^[a-z]\d+", lower):
            pass

        #
        # Skip obvious metadata
        #

        if lower.endswith(":"):
            continue

        if looks_like_written_by(line):
            continue

        #
        # Various Artists
        #

        if various:
            pair = split_various(line)

            if pair is None:
                continue

            artist, title = pair

            tracks.append({
                "artist": artist,
                "title": remove_time(title)
            })

        #
        # Standard album
        #

        else:
            for chunk in split_inline_tracks(line):
                title = chunk

                pieces = title.split()
                if not pieces:
                    continue

                if looks_like_track_code(pieces[0]) or re.match(r"^[A-Z]\d+", pieces[0], re.I):
                    title = " ".join(pieces[1:])
                elif not re.match(r"^[A-Z]{1,3}\d+", title, re.I):
                    if re.match(r"^[A-Z][A-Za-z0-9 '&.-]+$", title) and title.lower() not in {"genre", "style", "year", "released", "country", "format", "label", "more images"}:
                        pass
                    else:
                        continue

                title = remove_time(title)

                if not title:
                    continue

                tracks.append({
                    "artist": album_artist,
                    "title": title
                })

    return {
        "album": album,
        "album_artist": album_artist,
        "year": year,
        "various": various,
        "tracks": tracks
    }


#
# Simple test
#

if __name__ == "__main__":

    sample = """
Orleans – Orleans

Genre:
Rock

Style:
Pop Rock

Year:
1973

Please Be There    3:48
If    5:02
Two Faced World    4:30
Turn Out The Light    5:18
"""

    result = parse_discogs(sample)

    from pprint import pprint

    pprint(result)