import unittest

from pydantic import ValidationError

from docucite.schemas import Chunk, Document, Location, ParsedBlock, TableData


class SchemaTests(unittest.TestCase):
    def test_document_identity_and_supported_formats(self):
        first = Document(filename="通知.pdf", file_type="pdf")
        second = Document(filename="通知.pdf", file_type="pdf")
        self.assertNotEqual(first.doc_id, second.doc_id)
        for changes in ({"filename": " "}, {"file_type": "exe"}, {"unknown": True}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                Document.model_validate(dict(filename="通知.pdf", file_type="pdf") | changes)

    def test_locations_without_invented_pages(self):
        for fields in ({"heading_path": ["招聘", "条件"]}, {"paragraph_index": 3}):
            self.assertIsNone(Location(**fields).page)
        self.assertEqual(Location(page=2, page_end=3).page_end, 3)

    def test_invalid_locations(self):
        for fields in ({}, {"page": 0}, {"page": True}, {"page": 1.5},
                       {"page_end": 2}, {"page": 3, "page_end": 2},
                       {"row_start": 1}, {"table_index": 1, "row_end": 2},
                       {"table_index": 1, "row_start": 3, "row_end": 2}):
            with self.subTest(fields=fields), self.assertRaises(ValidationError):
                Location(**fields)

    def test_table_preserves_empty_cells_and_missing_header(self):
        table = TableData(header=["姓名", "备注"], rows=[["张三", ""]])
        self.assertEqual(table.rows[0][1], "")
        self.assertIsNone(TableData(rows=[["张三", ""]]).header)

    def test_invalid_table_shapes(self):
        for fields in ({"rows": []}, {"rows": [[]]}, {"rows": [["a"], ["b", "c"]]},
                       {"header": ["a", "b"], "rows": [["c"]]}):
            with self.subTest(fields=fields), self.assertRaises(ValidationError):
                TableData(**fields)

    def test_parsed_block_content_rules(self):
        common = dict(doc_id="doc-1", location=Location(page=1))
        text = "  原文\n保留格式  "
        self.assertEqual(ParsedBlock(**common, kind="text", text=text).text, text)
        table = TableData(rows=[["内容"]])
        self.assertEqual(ParsedBlock(**common, kind="table", table=table).table, table)
        for fields in ({"kind": "text", "text": " "}, {"kind": "table"},
                       {"kind": "text", "text": "正文", "table": table}):
            with self.subTest(fields=fields), self.assertRaises(ValidationError):
                ParsedBlock(**common, **fields)

    def test_table_chunk_json_round_trip_preserves_citation(self):
        document = Document(filename="招聘.pdf", file_type="pdf")
        table = TableData(header=["岗位", "人数"], rows=[["教师", "2"]])
        location = Location(page=2, table_index=1, row_start=1, row_end=1)
        block = ParsedBlock(doc_id=document.doc_id, kind="table", table=table, location=location)
        chunk = Chunk(doc_id=document.doc_id, filename=document.filename, kind="table",
                      text="岗位: 教师；人数: 2", table=table, location=location,
                      source_block_ids=[block.block_id])
        restored = Chunk.model_validate_json(chunk.model_dump_json())
        self.assertEqual(restored, chunk)
        self.assertEqual(restored.source_block_ids, [block.block_id])
        self.assertEqual(restored.filename, document.filename)

    def test_chunk_requires_content_and_sources(self):
        common = dict(doc_id="doc-1", filename="通知.md", kind="text", text="正文",
                      location=Location(heading_path=["通知"]), source_block_ids=["block-1"])
        self.assertIsNone(Chunk(**common).location.page)
        for changes in ({"text": " "}, {"source_block_ids": []},
                        {"source_block_ids": ["block-1", "block-1"]},
                        {"kind": "table"}, {"table": TableData(rows=[["内容"]])}):
            with self.subTest(changes=changes), self.assertRaises(ValidationError):
                Chunk(**(common | changes))


if __name__ == "__main__":
    unittest.main()
