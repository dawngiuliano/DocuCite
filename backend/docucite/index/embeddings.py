"""调用 OpenAI 兼容接口生成文本向量。"""

from collections.abc import Sequence

from .config import EmbeddingConfig, load_embedding_config


class EmbeddingClient:
    """一个简单的 Embedding 客户端，支持 OpenAI 兼容中转站。"""

    def __init__(self, config: EmbeddingConfig | None = None):
        from openai import OpenAI

        self.config = config or load_embedding_config()
        arguments = {"api_key": self.config.api_key}
        if self.config.base_url:
            arguments["base_url"] = self.config.base_url
        self.client = OpenAI(**arguments)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """把多条文本转换成向量，并保持输入顺序。"""
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise ValueError("Embedding 文本不能是空白")
        response = self.client.embeddings.create(model=self.config.model, input=list(texts))
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]
