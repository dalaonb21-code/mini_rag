from .sources.news_crawler import NewsCrawler
from .sources.policy_crawler import PolicyCrawler
from .sources.price_fetcher import PriceFetcher
from .processors.cleaner import clean_batch
from .processors.deduplicator import Deduplicator
from .processors.chunker import chunk_batch
from .embedder import Embedder
from .storage.faiss_writer import write_to_faiss


def run_pipeline(days: int = 30, limit: int = 200):
    print("=" * 60)
    print("Mining RAG Pipeline — 开始采集")
    print("=" * 60)

    # 1. 采集
    print("\n[1/5] 采集新闻...")
    news = NewsCrawler(days=days, limit=limit).fetch()
    print(f"  → 获取 {len(news)} 条新闻")

    print("[1/5] 采集政策...")
    policy = PolicyCrawler(days=days, limit=limit).fetch()
    print(f"  → 获取 {len(policy)} 条政策")

    print("[1/5] 采集价格...")
    price = PriceFetcher(days=days, limit=limit).fetch()
    print(f"  → 获取 {len(price)} 条价格")

    all_docs = news + policy + price
    print(f"\n  总计原始文档: {len(all_docs)} 条")

    # 2. 清洗
    print("\n[2/5] 清洗...")
    cleaned = clean_batch(all_docs)
    print(f"  → 清洗后: {len(cleaned)} 条")

    # 3. 去重
    print("\n[3/5] 去重...")
    dedup = Deduplicator()
    unique = dedup.filter(cleaned)
    print(f"  → 去重后: {len(unique)} 条")

    # 4. 切分
    print("\n[4/5] 切分...")
    chunks = chunk_batch(unique)
    print(f"  → 生成 {len(chunks)} 个 chunk")

    # 5. 向量化 + 入库
    print("\n[5/5] 向量化 + 写入 FAISS...")
    texts = [c["content"] for c in chunks]
    print(f"  → 待向量化文本: {len(texts)} 条")
    if not texts:
        print("  → 没有数据，跳过")
        return
    try:
        embedder = Embedder()
        vectors = embedder.encode_batch(texts)
        print(f"  → 向量化完成, shape={vectors.shape}")
        write_to_faiss(chunks, vectors)
    except Exception as e:
        import traceback
        print(f"\n[ERROR] 写入失败:")
        traceback.print_exc()
        return
    print(f"\n{'=' * 60}")
    print(f"完成! 共写入 {len(chunks)} 条记录到 FAISS")
    print(f"{'=' * 60}")
