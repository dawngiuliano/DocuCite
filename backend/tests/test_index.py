import tempfile
import unittest
from pathlib import Path

from docucite.index.metadata import load_metadata, save_metadata
from docucite.schemas import Chunk, Location


class MetadataTests(unittest.TestCase):
    def test_metadata_round_trip(self):
        chunk = Chunk(doc_id="doc-1", filename="a.md", kind="text", text="内容",
                      location=Location(page=1), source_block_ids=["block-1"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "metadata.json"
            save_metadata(path, [chunk])
            restored = load_metadata(path)
        self.assertEqual(restored, [chunk])
        self.assertEqual(len(restored), 1)


if __name__ == "__main__":
    unittest.main()
