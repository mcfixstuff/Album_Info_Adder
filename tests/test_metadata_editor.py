import tempfile
import unittest
from pathlib import Path

from metadata_editor import build_metadata_payload, get_opus_files


class MetadataEditorTests(unittest.TestCase):
    def test_get_opus_files_returns_sorted_opus_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, "02.opus").write_bytes(b"")
            Path(tmpdir, "01.opus").write_bytes(b"")
            Path(tmpdir, "notes.txt").write_text("ignore")

            files = get_opus_files(tmpdir)

            self.assertEqual([p.name for p in files], ["01.opus", "02.opus"])

    def test_build_metadata_payload_normalizes_tag_values(self):
        payload = build_metadata_payload({
            "TITLE": ["Song"],
            "ARTIST": ["Artist"],
            "ALBUMARTIST": ["Various Artists"],
            "ALBUM": ["Album"],
            "DATE": ["2024"],
            "TRACKNUMBER": ["3"],
        })

        self.assertEqual(payload["title"], "Song")
        self.assertEqual(payload["artist"], "Artist")
        self.assertEqual(payload["albumartist"], "Various Artists")
        self.assertEqual(payload["tracknumber"], "3")


if __name__ == "__main__":
    unittest.main()
