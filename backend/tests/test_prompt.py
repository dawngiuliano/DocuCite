import unittest

from docucite.chain.prompt import SYSTEM_PROMPT, build_messages
from docucite.index.retriever import SearchResult
from docucite.schemas import Chunk, Location


class PromptTests(unittest.TestCase):
    def test_messages_include_question_and_source_details(self):
        result = SearchResult(
            chunk=Chunk(
                doc_id="doc-1",
                filename="公告.md",
                kind="text",
                text="报名时间为 6 月 10 日。",
                location=Location(heading_path=["报名时间"]),
                source_block_ids=["block-1"],
            ),
            score=0.88,
        )
        messages = build_messages("什么时候报名？", [result])
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn(SYSTEM_PROMPT, messages[0]["content"])
        self.assertIn("什么时候报名？", messages[1]["content"])
        self.assertIn("公告.md", messages[1]["content"])
        self.assertIn("报名时间为 6 月 10 日。", messages[1]["content"])

    def test_empty_results_explicitly_say_no_reference(self):
        messages = build_messages("没有资料的问题", [])
        self.assertIn("没有检索到参考资料", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
