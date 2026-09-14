import unittest

from pydantic import ValidationError

from docucite.chunking import chunk_blocks
from docucite.schemas import Document, Location, ParsedBlock, TableData


class ChunkingTests(unittest.TestCase):
    def setUp(self):
        self.document = Document(filename="通知.md", file_type="md")

    def text_block(self, text, paragraph_index=1):
        return ParsedBlock(
            doc_id=self.document.doc_id,
            kind="text",
            text=text,
            location=Location(paragraph_index=paragraph_index),
        )

    def table_block(self):
        return ParsedBlock(
            doc_id=self.document.doc_id,
            kind="table",
            table=TableData(
                header=["岗位", "人数"],
                rows=[["教师", "2"], ["管理员", "1"]],
            ),
            location=Location(heading_path=["岗位表"], table_index=1),
        )

    def test_short_paragraphs_are_merged(self):
        blocks = [self.text_block("第一段"), self.text_block("第二段", 2)]
        chunks = chunk_blocks(self.document, blocks, max_chars=20, overlap=0)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].text, "第一段\n\n第二段")
        self.assertEqual(chunks[0].source_block_ids, [blocks[0].block_id, blocks[1].block_id])

    def test_long_text_is_split_with_overlap(self):
        block = self.text_block("1234567890")
        chunks = chunk_blocks(self.document, [block], max_chars=6, overlap=2)
        self.assertEqual([chunk.text for chunk in chunks], ["123456", "567890"])
        self.assertTrue(all(len(chunk.text) <= 6 for chunk in chunks))

    def test_multiple_paragraphs_from_one_block_have_one_source_id(self):
        block = self.text_block("第一段\n\n第二段")
        chunks = chunk_blocks(self.document, [block], max_chars=20, overlap=0)
        self.assertEqual(chunks[0].source_block_ids, [block.block_id])

    def test_table_creates_one_chunk_per_row_and_repeats_header(self):
        block = self.table_block()
        chunks = chunk_blocks(self.document, [block])
        table_chunks = [chunk for chunk in chunks if chunk.kind == "table"]
        self.assertEqual(len(table_chunks), 2)
        self.assertIn("表头：岗位 | 人数", table_chunks[0].text)
        self.assertIn("数据：教师 | 2", table_chunks[0].text)
        self.assertEqual(table_chunks[1].location.row_start, 2)
        self.assertEqual(table_chunks[0].table.rows, [["教师", "2"]])

    def test_empty_text_blocks_are_ignored(self):
        # ParsedBlock 本身拒绝空文本，这里用只有空白的文本也应由模型拒绝。
        with self.assertRaises(ValidationError):
            self.text_block(" ")

    def test_document_id_must_match(self):
        other = Document(filename="其他.md", file_type="md")
        block = ParsedBlock(
            doc_id=other.doc_id,
            kind="text",
            text="内容",
            location=Location(paragraph_index=1),
        )
        with self.assertRaises(ValueError):
            chunk_blocks(self.document, [block])

    def test_split_parameters_are_validated(self):
        block = self.text_block("内容")
        for max_chars, overlap in [(0, 0), (-1, 0), (10, -1), (10, 10), (10, 11)]:
            with self.subTest(max_chars=max_chars, overlap=overlap):
                with self.assertRaises(ValueError):
                    chunk_blocks(self.document, [block], max_chars, overlap)


if __name__ == "__main__":
    unittest.main()
