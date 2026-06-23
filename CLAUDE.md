# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mining RAG Pipeline — 矿业领域 RAG 系统，聚合新闻、政策、价格三源数据，支持自然语言查询。

## Commands

```bash
# 数据管线：采集 → 清洗 → 去重 → 向量化 → 写入 FAISS
python main.py pipeline --days 30 --limit 200

# 启动 API 服务（默认 8000，建议 8001 避免端口冲突）
python main.py serve --port 8001

# 运行评估（需要 serve 在运行）
python main.py eval
```

## Environment

必须创建 `.env` 文件（参考 `.env.example`）：
- `OPENAI_API_KEY` / `OPENAI_BASE_URL` / `LLM_MODEL` — LLM 配置（当前用 DeepSeek）
- `BGE_M3_PATH` — 本地 embedding 模型路径（必填，避免连 HuggingFace）
- `FAISS_DATA_DIR` — FAISS 数据目录（默认 `data`）

Windows 必须设置的环境变量（已在 main.py 和 serve/main.py 中设置）：
- `KMP_DUPLICATE_LIB_OK=TRUE`
- `PYTORCH_NO_SHARED_MEMORY=1`

## Architecture

```
main.py                    # CLI 入口：pipeline / serve / eval
├── pipeline/
│   ├── sources/
│   │   ├── base.py        # RawDocument dataclass + BaseCrawler ABC
│   │   ├── news_crawler.py    # mining.com RSS + 全文爬取
│   │   ├── policy_crawler.py  # 中国稀土集团 + 澳洲 DISR（失败时 mock 兜底）
│   │   └── price_fetcher.py   # LME/SHFE/Mysteel（无 API Key 时 mock）
│   ├── processors/
│   │   ├── cleaner.py     # 去 HTML、规范化空白、截断 4000 字符、过滤 <50 字符
│   │   ├── deduplicator.py # MinHash + LSH 去重（threshold=0.85）
│   │   └── chunker.py     # 滑动窗口切分（800 字符，100 重叠）
│   ├── embedder.py        # bge-small-zh-v1.5 直接 transformers 调用，batch_size=4
│   ├── storage/
│   │   ├── schema.py      # FAISS 数据布局，DIM=512
│   │   └── faiss_writer.py # IndexIDMap + IndexFlatIP，append 模式
│   └── run_pipeline.py    # 管线编排
├── serve/
│   ├── main.py            # FastAPI app，加载 .env
│   ├── retriever.py       # FAISS 向量 + BM25 + RRF 混合检索
│   ├── re_ranker.py       # LLM 重排序
│   ├── generator.py       # DeepSeek/OpenAI 回答生成
│   ├── augmentor.py       # 上下文构建
│   └── query_classifier.py # 关键词分类（news/policy/price）
└── eval/
    ├── ground_truth.jsonl # 20 条 Q&A
    ├── run_eval.py        # recall@5 + faithfulness（jieba 分词）
    └── report.py          # Markdown 报告
```

## Key Technical Decisions

- **Embedding**: bge-small-zh-v1.5 (512 维)，用 `AutoModel` 直接调用而非 SentenceTransformer/FlagEmbedding（后者在 Windows CPU 上会崩溃或 OOM）
- **向量库**: FAISS（IndexIDMap + IndexFlatIP），余弦相似度通过 L2 归一化 + 内积实现
- **LLM**: 通过 OpenAI SDK 调用 DeepSeek API，兼容 OpenAI 格式
- **去重**: MinHash + LSH，但中文文本的 `.split()` 分词效果有限，对短文本去重不理想
- **内存**: 8GB RAM 环境，embedding batch_size=4，不用 fp16（CPU fp16 反而更耗内存）
