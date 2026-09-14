"""使用 data/samples 中的真实文件测试解析器和切块器。

可以在 backend 目录直接运行：

    python tests/test_samples.py -v

也可以从仓库根目录运行：

    python backend/tests/test_samples.py -v
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


# 允许从 backend/ 或仓库根目录直接运行这个文件。
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from docucite.chunking import chunk_blocks  # noqa: E402
from docucite.ingest import parse_document  # noqa: E402


REPOSITORY_DIR = BACKEND_DIR.parent
SAMPLES_DIR = REPOSITORY_DIR / "data" / "samples"


class SampleFileTests(unittest.TestCase):
    """验证真实样例文件能够完成“解析 -> 切块”。"""

    def assert_valid_result(self, path: Path, expected_type: str) -> None:
        """检查一个样例文件的基本输出是否符合数据约定。"""
        document, blocks = parse_document(path)
        chunks = chunk_blocks(document, blocks)

        self.assertEqual(document.filename, path.name)
        self.assertEqual(document.file_type, expected_type)
        self.assertGreater(len(blocks), 0, f"{path.name} 没有解析出任何 ParsedBlock")
        self.assertGreater(len(chunks), 0, f"{path.name} 没有生成任何 Chunk")

        for block in blocks:
            self.assertEqual(block.doc_id, document.doc_id)

        for chunk in chunks:
            self.assertEqual(chunk.doc_id, document.doc_id)
            self.assertEqual(chunk.filename, document.filename)
            self.assertTrue(chunk.text.strip())
            self.assertGreater(len(chunk.source_block_ids), 0)

    def test_markdown_samples(self):
        files = sorted((SAMPLES_DIR / "markdown").glob("*.md"))
        self.assertGreater(len(files), 0, "data/samples/markdown 中没有 Markdown 样例")
        for path in files:
            with self.subTest(file=path.name):
                self.assert_valid_result(path, "md")

    def test_word_samples(self):
        files = sorted((SAMPLES_DIR / "word").glob("*.docx"))
        self.assertGreater(len(files), 0, "data/samples/word 中没有 Word 样例")
        for path in files:
            with self.subTest(file=path.name):
                self.assert_valid_result(path, "docx")

    def test_excel_samples(self):
        files = sorted((SAMPLES_DIR / "excel").glob("*.xlsx"))
        self.assertGreater(len(files), 0, "data/samples/excel 中没有 Excel 样例")
        for path in files:
            with self.subTest(file=path.name):
                self.assert_valid_result(path, "xlsx")

    @unittest.skipUnless(
        importlib.util.find_spec("pdfplumber"),
        "未安装 pdfplumber，执行 python -m pip install pdfplumber 后再测试 PDF",
    )
    def test_pdf_samples(self):
        files = sorted((SAMPLES_DIR / "pdf").glob("*.pdf"))
        self.assertGreater(len(files), 0, "data/samples/pdf 中没有 PDF 样例")
        for path in files:
            with self.subTest(file=path.name):
                self.assert_valid_result(path, "pdf")


if __name__ == "__main__":
    unittest.main(verbosity=2)
