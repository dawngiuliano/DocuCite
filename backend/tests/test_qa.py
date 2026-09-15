import unittest

from docucite.chain import GroundedQA, NO_EVIDENCE_ANSWER
from docucite.index.retriever import SearchResult
from docucite.schemas import Chunk, Location


class FakeRetriever:
    def __init__(self, results):
        self.results = results
        self.question = None
        self.top_k = None

    def search(self, question, top_k=5):
        self.question = question
        self.top_k = top_k
        return self.results


class FakeChatClient:
    def __init__(self, answer="根据资料，教师岗位招聘 2 人。"):
        self.answer = answer
        self.messages = None

    def complete(self, messages):
        self.messages = messages
        return self.answer


def result(text, score):
    return SearchResult(
        chunk=Chunk(
            doc_id="doc-1",
            filename="notice.md",
            kind="text",
            text=text,
            location=Location(heading_path=["招聘公告"]),
            source_block_ids=["block-1"],
        ),
        score=score,
    )


class GroundedQATests(unittest.TestCase):
    def test_ask_retrieves_evidence_calls_chat_and_returns_citations(self):
        retriever = FakeRetriever([result("教师岗位招聘 2 人", 0.91)])
        chat = FakeChatClient()
        qa = GroundedQA(retriever, chat, top_k=3, min_score=0.3)

        output = qa.ask("教师岗位招聘多少人？")

        self.assertEqual(retriever.question, "教师岗位招聘多少人？")
        self.assertEqual(retriever.top_k, 3)
        self.assertEqual(output.answer, "根据资料，教师岗位招聘 2 人。")
        self.assertEqual(len(output.citations), 1)
        self.assertEqual(output.citations[0].filename, "notice.md")
        self.assertEqual(output.citations[0].score, 0.91)
        self.assertIn("教师岗位招聘 2 人", chat.messages[1]["content"])

    def test_low_score_evidence_refuses_to_call_chat(self):
        retriever = FakeRetriever([result("无关内容", 0.12)])
        chat = FakeChatClient()
        output = GroundedQA(retriever, chat, min_score=0.3).ask("问题")

        self.assertEqual(output.answer, NO_EVIDENCE_ANSWER)
        self.assertEqual(output.citations, [])
        self.assertIsNone(chat.messages)

    def test_blank_question_and_invalid_options_are_rejected(self):
        retriever = FakeRetriever([])
        chat = FakeChatClient()
        for top_k, min_score in [(0, 0.3), (-1, 0.3), (5, -1.1), (5, 1.1)]:
            with self.subTest(top_k=top_k, min_score=min_score):
                with self.assertRaises(ValueError):
                    GroundedQA(retriever, chat, top_k=top_k, min_score=min_score)
        qa = GroundedQA(retriever, chat)
        with self.assertRaises(ValueError):
            qa.ask("   ")


if __name__ == "__main__":
    unittest.main()
