import hashlib
from ..sources.base import RawDocument


def make_doc_id(doc: RawDocument) -> str:
    """基于 URL + 标题生成唯一主键"""
    raw = f"{doc.url}|{doc.title}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def chunk_doc(doc: RawDocument, max_len: int = 800, overlap: int = 100) -> list[dict]:
    """
    将长文档切分为多个 chunk，每个 chunk 是一个 dict：
    {
        "id": str,           # doc_id + chunk序号
        "source_type": str,
        "title": str,
        "content": str,      # chunk文本
        "url": str,
        "published_ts": int, # unix timestamp
    }
    短文档（<=max_len）直接返回单 chunk。
    """
    doc_id = make_doc_id(doc)
    pub_ts = int(doc.published_at.timestamp()) if doc.published_at else 0
    text = doc.content

    if len(text) <= max_len:
        return [
            {
                "id": doc_id,
                "source_type": doc.source_type,
                "title": doc.title,
                "content": text,
                "url": doc.url,
                "published_ts": pub_ts,
            }
        ]

    chunks = []
    start = 0
    idx = 0
    while start < len(text):
        end = start + max_len
        chunk_text = text[start:end]
        chunks.append(
            {
                "id": f"{doc_id}_{idx}",
                "source_type": doc.source_type,
                "title": doc.title,
                "content": chunk_text,
                "url": doc.url,
                "published_ts": pub_ts,
            }
        )
        start += max_len - overlap
        idx += 1
    return chunks


def chunk_batch(docs: list[RawDocument]) -> list[dict]:
    """批量切分，返回所有 chunk 列表"""
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_doc(doc))
    return all_chunks
