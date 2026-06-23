"""
FAISS 存储管理 — 索引文件 + 元数据 JSON

文件布局:
    data/faiss_index.bin   — FAISS 向量索引
    data/metadata.json     — chunk 元数据列表 (与 FAISS 行号对齐)
"""

import json, os
from pathlib import Path

DATA_DIR = Path(os.getenv("FAISS_DATA_DIR", "data"))
INDEX_PATH = DATA_DIR / "faiss_index.bin"
META_PATH = DATA_DIR / "metadata.json"
DIM = 512   # bge-small-zh-v1.5 输出维度


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_metadata() -> list[dict]:
    """加载元数据列表"""
    if not META_PATH.exists():
        return []
    return json.loads(META_PATH.read_text(encoding="utf-8"))


def save_metadata(meta: list[dict]):
    """保存元数据列表"""
    ensure_data_dir()
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
