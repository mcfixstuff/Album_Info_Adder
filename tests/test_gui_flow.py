import tempfile
import unittest
from pathlib import Path

from gui import build_preview_rows
from parser import parse_discogs
from tagger import build_target_filename, rename_files


class BuildPreviewRowsTests(unittest.TestCase):
    def test_build_preview_rows_parses_discogs_and_returns_rows(self):
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
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "01.opus").write_bytes(b"")
            Path(tmpdir, "02.opus").write_bytes(b"")

            album_data, rows = build_preview_rows(sample, tmpdir)

            self.assertEqual(album_data["album"], "Orleans")
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["title"], "Please Be There")

    def test_build_target_filename_uses_track_number_and_title(self):
        track = {"title": "My Song"}
        self.assertEqual(build_target_filename(1, track), "01 My Song.opus")

    def test_parse_discogs_handles_markdown_style_track_listing(self):
        sample = """
# [Boots Randolph](https://www.discogs.com/artist/48398-Boots-Randolph) – Boots Randolph's Yakety Sax!
## Released:
## Genre:
[Jazz](https://www.discogs.com/genre/jazz)
## Style:
A1Yakety SaxWritten-By – [Randolph](https://www.discogs.com/artist/48398-Boots-Randolph)*, [Rich](https://www.discogs.com/artist/900388-James-Rich)*
2:00A2Walk Right InWritten-By – [Darling](https://www.discogs.com/artist/794536-Erik-Darling)*, [Svanoe](https://www.discogs.com/artist/1104095-Willard-Svanoe)*
"""

        album_data = parse_discogs(sample)

        self.assertEqual(album_data["album"], "Boots Randolph's Yakety Sax!")
        self.assertEqual(album_data["album_artist"], "Boots Randolph")
        self.assertEqual(len(album_data["tracks"]), 2)
        self.assertEqual(album_data["tracks"][0]["title"], "Yakety Sax")
        self.assertEqual(album_data["tracks"][1]["title"], "Walk Right In")

    def test_rename_files_renames_opus_files_to_track_titles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir, "track1.opus")
            source.write_bytes(b"")

            album_data = {"tracks": [{"title": "My Song"}]}
            renamed = rename_files(tmpdir, album_data)

            self.assertEqual(renamed, 1)
            self.assertTrue(Path(tmpdir, "01 My Song.opus").exists())
            self.assertFalse(source.exists())


if __name__ == "__main__":
    unittest.main()
