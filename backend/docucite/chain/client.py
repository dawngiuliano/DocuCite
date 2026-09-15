"""聊天模型客户端。"""

from collections.abc import Sequence

from ..index.config import ChatConfig, load_chat_config


class ChatClient:
    """调用 OpenAI 兼容的聊天接口。"""

    def __init__(self, config: ChatConfig | None = None):
        from openai import OpenAI

        self.config = config or load_chat_config()
        arguments = {"api_key": self.config.api_key}
        if self.config.base_url:
            arguments["base_url"] = self.config.base_url
        self.client = OpenAI(**arguments)

    def complete(self, messages: Sequence[dict[str, str]]) -> str:
        """发送消息并返回聊天模型的纯文本回答。"""
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=list(messages),
            temperature=0,
        )
        content = response.choices[0].message.content
        if not content or not content.strip():
            raise ValueError("聊天模型返回了空答案")
        return content.strip()
