import unittest

from docucite.index.retriever import IndexRetriever
from docucite.schemas import Chunk, Location


class FakeEmbedder:
    def __init__(self, vectors):
        self.vectors = vectors
        self.questions = []

    def embed(self, texts):
        self.questions.extend(texts)
        return self.vectors


class FakeStore:
    def __init__(self, matches):
        self.matches = matches
        self.vector = None
        self.top_k = None

    def search(self, vector, top_k):
        self.vector = vector
        self.top_k = top_k
        return self.matches[:top_k]


def make_chunk(text):
    return Chunk(
        doc_id="doc-1",
        filename="notice.md",
        kind="text",
        text=text,
        location=Location(heading_path=["公告"]),
        source_block_ids=[f"block-{text}"],
    )


class RetrieverTests(unittest.TestCase):
    def test_search_embeds_question_and_returns_scored_chunks(self):
        first = make_chunk("教师岗位招聘人数为 2 人")
        second = make_chunk("报名时间为六月")
        embedder = FakeEmbedder([[0.1, 0.2]])
        store = FakeStore([(first, 0.91), (second, 0.72)])
        retriever = IndexRetriever(store, embedder)

        results = retriever.search("教师岗位有多少人？", top_k=1)

        self.assertEqual(embedder.questions, ["教师岗位有多少人？"])
        self.assertEqual(store.vector, [0.1, 0.2])
        self.assertEqual(store.top_k, 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].chunk, first)
        self.assertEqual(results[0].score, 0.91)

    def test_search_rejects_invalid_question_and_top_k(self):
        retriever = IndexRetriever(FakeStore([]), FakeEmbedder([[0.1]]))
        for question, top_k in [("", 5), ("   ", 5), ("问题", 0), ("问题", -1)]:
            with self.subTest(question=question, top_k=top_k), self.assertRaises(ValueError):
                retriever.search(question, top_k)

    def test_search_requires_one_query_vector(self):
        retriever = IndexRetriever(FakeStore([]), FakeEmbedder([[0.1], [0.2]]))
        with self.assertRaises(ValueError):
            retriever.search("问题")


if __name__ == "__main__":
    unittest.main()
