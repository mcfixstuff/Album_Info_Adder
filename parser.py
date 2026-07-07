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


def split_compact_track_list(text):
    """Split a compact track list like 'A1SongA2Song2' into separate titles."""

    text = text.strip()
    if not text:
        return []

    matches = list(re.finditer(r"[A-Z]?\d+[A-Z]?", text, re.I))
    if not matches:
        return []

    chunks = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = text[start:end].strip()
        title = re.sub(r"^[^A-Za-z0-9']+", "", title)
        if title:
            chunks.append(title)
    return chunks


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


def extract_artist_album(line):
    """Extract artist/album from a header line like 'Artist – Album'."""

    candidate = clean_line(line)
    if not candidate:
        return None

    lowered = candidate.lower()
    if lowered.startswith(("genre:", "style:", "year:", "released:", "label:", "format:", "country:", "more images")):
        return None
    if "album cover" in lowered or "cover" in lowered and lowered.endswith("cover"):
        pass

    match = re.match(r"^(?P<artist>.+?)\s*(?:–|—|-|/|:)\s*(?P<album>.+)$", candidate)
    if not match:
        return None

    artist = clean_line(match.group("artist")).rstrip("*")
    album = clean_line(match.group("album"))
    album = re.sub(r"\s+(album cover|cover)$", "", album, flags=re.I)
    album = album.strip(" .")

    if not artist or not album:
        return None

    if artist.lower() in {"genre", "style", "year", "released", "country", "format", "label", "more images"}:
        return None

    return artist, album


def remove_time(title):
    """
    Removes trailing runtimes in the form 3:48 or 03:48.
    """

    title = re.sub(r"\s+\d{1,2}:\d{2}$", "", title).strip()
    return title


def looks_like_written_by(text):
    return bool(re.search(r"written-by", text, re.I))


def split_inline_tracks(text, keep_numeric_titles=False):
    """Split a line like 'Song 1 3:29Song 2 4:21' into title chunks."""

    text = text.strip()
    if not text:
        return []

    if re.fullmatch(r"\d{1,2}:\d{2}", text):
        return [text] if keep_numeric_titles else []

    if re.search(r"\d{1,2}:\d{2}", text):
        chunks = []
        for match in re.finditer(r"(?P<title>.+?)(?P<runtime>\d{1,2}:\d{2})(?=(?:.+?\d{1,2}:\d{2})|$)", text):
            title = match.group("title").strip()
            if title:
                chunks.append(title)
        return chunks

    return [text]


def split_track_segments(text, ignore_commas=False, ignore_parentheses=False):
    """Split a line into multiple track-like chunks when requested.

    When the user opts to ignore commas or parentheses, keep the full text intact
    so titles such as 'Could You Love A Poor Boy, Dolly' stay together.
    """

    text = text.strip()
    if not text:
        return []

    if ignore_commas or ignore_parentheses:
        return [text]

    if "," in text:
        parts = [part.strip() for part in re.split(r"\s*,\s*", text) if part.strip()]
        if len(parts) > 1:
            return parts

    return [text]


def parse_discogs(text, ignore_commas=False, ignore_parentheses=False, keep_numeric_titles=False, handle_track_codes=False):

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
        header = extract_artist_album(line)
        if header:
            album_artist, album = header
            break

    if not album_artist and lines:
        first = lines[0]
        header = extract_artist_album(first)
        if header:
            album_artist, album = header

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
            if handle_track_codes and re.search(r"[A-Z]?\d+[A-Z]?", line, re.I):
                compact_chunks = split_compact_track_list(line)
                if compact_chunks:
                    for chunk in compact_chunks:
                        title = chunk.strip()
                        title = re.sub(r"^[A-Z]?\d+[A-Z]?", "", title, flags=re.I)
                        title = remove_time(title)
                        if title and re.search(r"[A-Za-z]", title):
                            tracks.append({
                                "artist": album_artist,
                                "title": title.strip()
                            })
                    continue

            for segment in split_track_segments(line, ignore_commas=ignore_commas, ignore_parentheses=ignore_parentheses):
                for chunk in split_inline_tracks(segment, keep_numeric_titles=keep_numeric_titles):
                    title = chunk

                    pieces = title.split()
                    if not pieces:
                        continue

                    if not keep_numeric_titles and (looks_like_track_code(pieces[0]) or re.match(r"^[A-Z]\d+", pieces[0], re.I)):
                        title = " ".join(pieces[1:])
                    elif not keep_numeric_titles and re.match(r"^\d+(?:\.\d+)?(?:\s|$)", title):
                        title = re.sub(r"^\d+(?:\.\d+)?\s*", "", title)

                    title = remove_time(title)

                    if not title:
                        continue

                    normalized = title.strip().lower()
                    if normalized in {"genre", "style", "year", "released", "country", "format", "label", "more images"}:
                        continue
                    if not re.search(r"[A-Za-z]", title):
                        continue

                    title = title.strip()

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