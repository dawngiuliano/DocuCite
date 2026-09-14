"""FAISS 索引和 Chunk 元数据的持久化。"""

from pathlib import Path
from typing import Callable

import numpy as np

from ..schemas import Chunk
from .metadata import load_metadata, save_metadata


class FaissStore:
    """用内积相似度保存和检索切片向量。"""

    def __init__(self, index, chunks: list[Chunk]):
        self.index = index
        self.chunks = chunks

    @classmethod
    def build(cls, chunks: list[Chunk], embed: Callable[[list[str]], list[list[float]]]) -> "FaissStore":
        """为切片生成向量并创建索引。"""
        import faiss

        if not chunks:
            raise ValueError("不能为空切片列表创建索引")
        vectors = np.asarray(embed([chunk.text for chunk in chunks]), dtype="float32")
        if vectors.ndim != 2 or len(vectors) != len(chunks):
            raise ValueError("Embedding 返回的向量数量或维度不正确")
        faiss.normalize_L2(vectors)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index, chunks)

    def search(self, vector: list[float], top_k: int = 5) -> list[tuple[Chunk, float]]:
        """检索最相似的切片，返回 Chunk 和相似度。"""
        if top_k <= 0:
            raise ValueError("top_k 必须大于 0")
        query = np.asarray([vector], dtype="float32")
        import faiss
        faiss.normalize_L2(query)
        scores, indexes = self.index.search(query, min(top_k, self.index.ntotal))
        return [(self.chunks[i], float(score)) for i, score in zip(indexes[0], scores[0]) if i >= 0]

    def save(self, directory: str | Path) -> None:
        """保存 index.faiss 和 metadata.json。"""
        import faiss
        target = Path(directory); target.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(target / "index.faiss"))
        save_metadata(target / "metadata.json", self.chunks)

    @classmethod
    def load(cls, directory: str | Path) -> "FaissStore":
        """从磁盘加载索引和切片。"""
        import faiss
        target = Path(directory)
        return cls(faiss.read_index(str(target / "index.faiss")), load_metadata(target / "metadata.json"))
