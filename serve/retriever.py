import json
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from pipeline.storage.schema import INDEX_PATH, META_PATH, load_metadata


class HybridRetriever:
    def __init__(self, embedder, top_k: int = 20):
        self.embedder = embedder
        self.top_k = top_k

        # 加载 FAISS 索引
        if INDEX_PATH.exists():
            self.index = faiss.read_index(str(INDEX_PATH))
        else:
            raise FileNotFoundError(f"FAISS 索引不存在: {INDEX_PATH}，请先运行 pipeline")

        # 加载元数据
        self.meta = load_metadata()
        if not self.index.ntotal == len(self.meta):
            print(f"[WARN] FAISS({self.index.ntotal}) 与 metadata({len(self.meta)}) 数量不匹配")

        # 构建 BM25
        self._build_bm25()

    def _build_bm25(self):
        """用元数据中的 content 构建 BM25 索引"""
        corpus = [m["content"].split() for m in self.meta]
        self.bm25 = BM25Okapi(corpus)

    def retrieve(self, query: str, top_k: int = 5, source_type: str = "") -> list[dict]:
        # --- BM25 ---
        bm25_scores = self.bm25.get_scores(query.split())
        bm25_top_k = min(self.top_k, len(bm25_scores))
        bm25_top = np.argsort(bm25_scores)[::-1][:bm25_top_k]

        # --- 向量检索 ---
        q_vec = self.embedder.encode_batch([query])
        faiss.normalize_L2(q_vec)
        search_k = min(self.top_k, self.index.ntotal)
        scores, indices = self.index.search(q_vec, search_k)

        # --- source_type 过滤（向量侧） ---
        vec_hits = {}
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            m = self.meta[idx]
            if source_type and m["source_type"] != source_type:
                continue
            vec_hits[idx] = {"score": float(score), "meta": m, "idx": idx}

        # --- RRF 融合 ---
        rrf_scores: dict[int, float] = {}

        # BM25 排名
        for rank, idx in enumerate(bm25_top):
            m = self.meta[idx]
            if source_type and m["source_type"] != source_type:
                continue
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (60 + rank + 1)

        # 向量排名
        for rank, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < 0:
                continue
            m = self.meta[idx]
            if source_type and m["source_type"] != source_type:
                continue
            rrf_scores[idx] = rrf_scores.get(idx, 0) + 1 / (60 + rank + 1)

        sorted_idxs = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]

        # 回填完整字段
        results = []
        for idx in sorted_idxs:
            m = self.meta[idx]
            results.append({
                "id": m["id"],
                "title": m["title"],
                "content": m["content"],
                "url": m["url"],
                "source_type": m["source_type"],
                "score": rrf_scores[idx],
            })
        return results
