import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from parser import parse_discogs
from tagger import preview


def test_ignore_commas_and_parentheses_as_separators():
    sample = """Artist – Album

Year:
2024

Song One, Song Two (feat. Artist)
Another Track
"""
    result = parse_discogs(sample, ignore_commas=True, ignore_parentheses=True)
    assert [track["title"] for track in result["tracks"]] == ["Song One", "Song Two", "Another Track"]


def test_keep_numeric_titles_but_strip_time_only_numbers():
    sample = """Artist – Album

Year:
2024

1. Song Title
2. Another Song
00:00
"""
    result = parse_discogs(sample, keep_numeric_titles=True)
    assert [track["title"] for track in result["tracks"]] == ["1. Song Title", "2. Another Song", "00:00"]


def test_ignore_punctuation_keeps_titles_with_commas_and_parentheses():
    sample = """Artist – Album

Year:
1976

Do You Right Tonight2:31I Can't Get This Ring Off My Finger2:45Rocky Mountain Music3:22Two Dollars In The Jukebox2:22I Don't Wanna Make Love (With Anyone But You)2:50I Just Got To Have You2:39Tullahoma Dancing Pizza Man2:39Ain't I Something2:14There's Someone She Lies To (To Lay Here With Me)3:22Could You Love A Poor Boy, Dolly2:49Drinkin' My Baby (Off My Mind)2:23"""
    result = parse_discogs(sample, ignore_commas=True, ignore_parentheses=True)
    titles = [track["title"] for track in result["tracks"]]
    assert "Could You Love A Poor Boy, Dolly" in titles
    assert "Drinkin' My Baby (Off My Mind)" in titles
    assert "Dolly" not in titles


def test_preview_error_includes_parsed_track_details(tmp_path):
    sample = {
        "album": "Demo Album",
        "album_artist": "Demo Artist",
        "year": "2024",
        "various": False,
        "tracks": [
            {"artist": "Demo Artist", "title": "Track One"},
            {"artist": "Demo Artist", "title": "Track Two"},
        ],
    }

    try:
        preview(str(tmp_path), sample)
    except ValueError as exc:
        message = str(exc)
        assert "Track One" in message
        assert "Track Two" in message
        assert "Demo Album" in message
    else:
        raise AssertionError("Expected a ValueError")
