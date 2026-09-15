import unittest

from fastapi.testclient import TestClient

from docucite.api.app import create_app
from docucite.chain import AnswerResult


class FakeService:
    def upload(self, filename, content):
        return {
            "doc_id": "doc-1",
            "filename": filename,
            "file_type": "md",
            "block_count": 1,
            "chunk_count": 1,
        }

    def list_documents(self):
        return [{"filename": "notice.md", "file_type": "md", "chunk_count": 2}]

    def ask(self, question, top_k=5, min_score=0.3):
        return AnswerResult(answer=f"回答：{question}")


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(create_app(FakeService()))

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_list_documents(self):
        response = self.client.get("/api/documents")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["filename"], "notice.md")

    def test_upload_document(self):
        response = self.client.post(
            "/api/documents",
            files={
                "file": (
                    "notice.md",
                    "# 公告\n\n内容".encode("utf-8"),
                    "text/markdown",
                )
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["chunk_count"], 1)

    def test_ask(self):
        response = self.client.post(
            "/api/ask",
            json={"question": "教师岗位招聘多少人？", "top_k": 3},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "回答：教师岗位招聘多少人？")

    def test_ask_rejects_invalid_options(self):
        response = self.client.post(
            "/api/ask",
            json={"question": "问题", "top_k": 0},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
