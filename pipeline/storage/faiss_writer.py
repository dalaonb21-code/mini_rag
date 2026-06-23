"""将 chunk + 向量写入 FAISS 索引 + 元数据 JSON"""

import json
import numpy as np
import faiss
from pathlib import Path
from .schema import ensure_data_dir, load_metadata, save_metadata, INDEX_PATH, DIM


def write_to_faiss(chunks: list[dict], vectors: np.ndarray):
    """
    写入流程:
      1. 若已有索引则追加（IndexIDMap → FlatIP）
      2. 元数据 JSON 与 FAISS 行号一一对应
    """
    ensure_data_dir()

    # 归一化向量（用内积做 cosine）
    faiss.normalize_L2(vectors)

    if INDEX_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))
        old_meta = load_metadata()
    else:
        index = faiss.IndexIDMap(faiss.IndexFlatIP(DIM))
        old_meta = []

    # 生成 int64 ID（用行号偏移）
    start_id = len(old_meta)
    ids = np.arange(start_id, start_id + len(chunks), dtype=np.int64)

    index.add_with_ids(vectors, ids)
    faiss.write_index(index, str(INDEX_PATH))

    # 追加元数据
    new_meta = old_meta + [
        {
            "id": c["id"],
            "source_type": c["source_type"],
            "title": c["title"],
            "content": c["content"][:4000],
            "url": c["url"],
            "published_ts": c["published_ts"],
        }
        for c in chunks
    ]
    save_metadata(new_meta)

    print(f"  → FAISS 写入完成，共 {index.ntotal} 条向量")
