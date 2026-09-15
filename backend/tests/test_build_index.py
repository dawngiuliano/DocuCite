import importlib.util
import tempfile
import unittest
from pathlib import Path

from scripts.build_index import collect_files, collect_chunks, build_index


class BuildIndexTests(unittest.TestCase):
    def test_collect_default_samples_and_filter_supported_suffixes(self):
        files = collect_files([Path("../data/samples")])
        self.assertGreaterEqual(len(files), 4)
        self.assertTrue(all(path.suffix.lower() in {".pdf", ".docx", ".md", ".xlsx"} for path in files))

    def test_collect_deduplicates_same_file(self):
        path = Path("../data/samples/markdown").glob("*.md").__next__()
        self.assertEqual(collect_files([path, path.resolve()]), [path.resolve()])

    def test_collect_rejects_missing_and_unsupported_files(self):
        with self.assertRaises(FileNotFoundError):
            collect_files(["../data/samples/missing.md"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.txt"
            path.write_text("not supported", encoding="utf-8")
            with self.assertRaises(ValueError):
                collect_files([path])

    def test_collect_chunks_uses_requested_split_parameters(self):
        path = Path("../data/samples/markdown").glob("*.md").__next__()
        chunks, block_count = collect_chunks([path], max_chars=200, overlap=20)
        self.assertGreater(block_count, 0)
        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(len(chunk.text) <= 200 for chunk in chunks))

    @unittest.skipUnless(importlib.util.find_spec("faiss"), "未安装 faiss-cpu，跳过本地索引构建测试")
    def test_build_index_with_local_fake_embeddings(self):
        path = Path("../data/samples/markdown").glob("*.md").__next__()

        def fake_embed(texts):
            return [[float(len(text)), 1.0, 0.0] for text in texts]

        with tempfile.TemporaryDirectory() as directory:
            summary = build_index([path], output_dir=directory, embed=fake_embed)
            self.assertEqual(summary.files, 1)
            self.assertTrue((Path(directory) / "index.faiss").exists())
            self.assertTrue((Path(directory) / "metadata.json").exists())


if __name__ == "__main__":
    unittest.main()
