"""读取聊天模型和向量模型的环境配置。"""

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class EmbeddingConfig:
    api_key: str
    base_url: str | None
    model: str


@dataclass(frozen=True)
class ChatConfig:
    """聊天模型中转站配置。"""

    api_key: str
    base_url: str | None
    model: str


def load_embedding_config(env_file: str | Path | None = None) -> EmbeddingConfig:
    """读取 Embedding 专用配置，不会误用聊天模型的 Key。"""
    path = Path(env_file) if env_file else Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(path)
    api_key = os.getenv("EMBEDDING_API_KEY", "").strip()
    model = os.getenv("EMBEDDING_MODEL", "").strip()
    if not api_key:
        raise ValueError("未配置 EMBEDDING_API_KEY")
    if not model:
        raise ValueError("未配置 EMBEDDING_MODEL")
    base_url = os.getenv("EMBEDDING_BASE_URL", "").strip() or None
    return EmbeddingConfig(api_key=api_key, base_url=base_url, model=model)


def load_chat_config(env_file: str | Path | None = None) -> ChatConfig:
    """读取聊天模型配置，不会误用 Embedding 的 Key。"""
    path = Path(env_file) if env_file else Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(path)
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "").strip()
    if not api_key:
        raise ValueError("未配置 OPENAI_API_KEY")
    if not model:
        raise ValueError("未配置 OPENAI_MODEL")
    base_url = os.getenv("OPENAI_BASE_URL", "").strip() or None
    return ChatConfig(api_key=api_key, base_url=base_url, model=model)
