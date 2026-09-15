"""把用户问题转换成向量，并从 FAISS 索引中找回相关切片。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Sequence

from ..schemas import Chunk
from .embeddings import EmbeddingClient
from .faiss_store import FaissStore


class Embedder(Protocol):
    """Embedding 客户端需要提供的最小接口，便于测试时注入假实现。"""

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        ...


@dataclass(frozen=True)
class SearchResult:
    """一条检索结果：切片内容和 FAISS 返回的相似度。"""

    chunk: Chunk
    score: float


class IndexRetriever:
    """加载一个索引，并提供按问题检索的接口。"""

    def __init__(self, store: FaissStore, embedder: Embedder):
        self.store = store
        self.embedder = embedder

    @classmethod
    def from_directory(
        cls,
        directory: str | Path,
        embedder: Embedder | None = None,
    ) -> "IndexRetriever":
        """从目录加载 FAISS 索引；未传客户端时读取 backend/.env。"""
        return cls(
            store=FaissStore.load(directory),
            embedder=embedder or EmbeddingClient(),
        )

    def search(self, question: str, top_k: int = 5) -> list[SearchResult]:
        """检索与问题最相关的切片，并按相似度从高到低返回。"""
        if not question.strip():
            raise ValueError("问题不能是空白")
        if top_k <= 0:
            raise ValueError("top_k 必须大于 0")

        vectors = self.embedder.embed([question])
        if len(vectors) != 1:
            raise ValueError("问题 Embedding 必须返回一个向量")
        matches = self.store.search(vectors[0], top_k=top_k)
        return [SearchResult(chunk=chunk, score=score) for chunk, score in matches]
