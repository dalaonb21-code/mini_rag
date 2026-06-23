import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["PYTORCH_NO_SHARED_MEMORY"] = "1"

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from pydantic import BaseModel
from .retriever import HybridRetriever
from .re_ranker import Reranker
from .generator import Generator
from .query_classifier import classify_query
from pipeline.embedder import Embedder

app = FastAPI(title="Mining RAG API")

# ---- 初始化组件（启动时一次） ----
print("[serve] 加载 Embedder...")
embedder = Embedder()

print("[serve] 初始化 Retriever (FAISS)...")
retriever = HybridRetriever(embedder)

print("[serve] 初始化 Reranker...")
reranker = Reranker()

print("[serve] 初始化 Generator...")
generator = Generator()

print("[serve] 就绪!")


# ---- 请求/响应模型 ----
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    query_type: str


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    q_type = classify_query(req.query)
    hits = retriever.retrieve(req.query, top_k=20, source_type=q_type)
    # 如果分类过滤后结果不足，回退到全量检索
    if len(hits) < 5:
        hits = retriever.retrieve(req.query, top_k=20)
    reranked = reranker.rerank(req.query, hits, top_k=req.top_k)
    answer = generator.generate(req.query, reranked)
    return QueryResponse(
        answer=answer,
        sources=[{"title": h["title"], "url": h["url"]} for h in reranked],
        query_type=q_type,
    )


@app.get("/health")
def health():
    return {"status": "ok", "vectors": retriever.index.ntotal}
