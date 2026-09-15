"""检索增强问答链。"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from pydantic import Field

from ..index.retriever import IndexRetriever, SearchResult
from ..schemas import Location, NonBlank, Schema
from .client import ChatClient
from .prompt import build_messages


NO_EVIDENCE_ANSWER = "根据现有文档，无法找到足够依据回答。"


class Retriever(Protocol):
    """问答链需要的最小检索接口。"""

    def search(self, question: str, top_k: int = 5) -> list[SearchResult]:
        ...


class Completer(Protocol):
    """聊天客户端需要的最小接口。"""

    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        ...


class Citation(Schema):
    """答案中的一条来源引用。"""

    filename: NonBlank
    location: Location
    snippet: NonBlank
    score: float = Field(ge=-1, le=1)


class AnswerResult(Schema):
    """问答链返回给 API 或命令行的结果。"""

    answer: NonBlank
    citations: list[Citation] = Field(default_factory=list)


class GroundedQA:
    """先检索证据，再调用聊天模型生成有引用的答案。"""

    def __init__(
        self,
        retriever: Retriever,
        chat_client: Completer,
        *,
        top_k: int = 5,
        min_score: float = 0.3,
    ):
        if top_k <= 0:
            raise ValueError("top_k 必须大于 0")
        if not -1 <= min_score <= 1:
            raise ValueError("min_score 必须在 -1 和 1 之间")
        self.retriever = retriever
        self.chat_client = chat_client
        self.top_k = top_k
        self.min_score = min_score

    @classmethod
    def from_directory(
        cls,
        index_dir: str | Path,
        *,
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> "GroundedQA":
        """从索引目录和 backend/.env 创建真实问答链。"""
        return cls(
            IndexRetriever.from_directory(index_dir),
            ChatClient(),
            top_k=top_k,
            min_score=min_score,
        )

    def ask(self, question: str) -> AnswerResult:
        """回答一个问题；没有足够相似的依据时拒绝编造。"""
        if not question.strip():
            raise ValueError("问题不能是空白")

        results = self.retriever.search(question, top_k=self.top_k)
        supported = [result for result in results if result.score >= self.min_score]
        if not supported:
            return AnswerResult(answer=NO_EVIDENCE_ANSWER)

        answer = self.chat_client.complete(build_messages(question, supported))
        citations = [
            Citation(
                filename=result.chunk.filename,
                location=result.chunk.location,
                snippet=result.chunk.text,
                score=result.score,
            )
            for result in supported
        ]
        return AnswerResult(answer=answer, citations=citations)
