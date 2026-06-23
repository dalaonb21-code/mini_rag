import re
from ..sources.base import RawDocument


def clean(doc: RawDocument) -> RawDocument:
    """清洗单条文档：去 HTML 残留、规范化空白、截断过长文本"""
    text = doc.content
    # 去 HTML 标签残留
    text = re.sub(r"<[^>]+>", "", text)
    # 规范化空白
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()
    # 截断到 4000 字符
    text = text[:4000]
    doc.content = text

    # 清洗标题
    doc.title = re.sub(r"\s+", " ", doc.title).strip()[:200]
    return doc


def clean_batch(docs: list[RawDocument]) -> list[RawDocument]:
    """批量清洗，跳过内容过短的文档"""
    cleaned = []
    for doc in docs:
        doc = clean(doc)
        if len(doc.content) >= 50:
            cleaned.append(doc)
    return cleaned
