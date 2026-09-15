"""生成基于检索证据的问答提示词。"""

from collections.abc import Sequence

from ..index.retriever import SearchResult


SYSTEM_PROMPT = """你是一个严谨的文档问答助手。
只能根据用户提供的参考资料回答，不得使用资料之外的常识补充答案。
如果参考资料不足以回答问题，请明确回答“根据现有文档，无法找到足够依据回答”。
回答要直接、简洁，并保留资料中的数字、日期和条件。
不要编造文件名、页码、标题或其他引用信息。"""


def build_messages(question: str, results: Sequence[SearchResult]) -> list[dict[str, str]]:
    """把问题和检索结果组织成聊天模型需要的消息列表。"""
    evidence_parts = []
    for number, result in enumerate(results, start=1):
        chunk = result.chunk
        location = chunk.location.model_dump(exclude_none=True)
        evidence_parts.append(
            f"[资料 {number}]\n"
            f"文件：{chunk.filename}\n"
            f"位置：{location}\n"
            f"相似度：{result.score:.4f}\n"
            f"内容：{chunk.text}"
        )
    evidence = "\n\n".join(evidence_parts) or "（没有检索到参考资料）"
    user_prompt = f"问题：{question.strip()}\n\n参考资料：\n{evidence}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
