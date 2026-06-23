# Mini RAG — 矿业领域三源聚合检索增强生成系统

一个面向矿业领域的 RAG（Retrieval-Augmented Generation）系统，聚合**新闻、政策、价格**三类数据源，支持中文自然语言查询。

## 功能

- **三源数据采集**：矿业新闻（mining.com）、行业政策（中国稀土集团/澳洲DISR）、金属价格（LME/SHFE/上海钢联）
- **智能检索**：向量检索 + BM25 关键词检索 + RRF 融合排序
- **自动问答**：基于 DeepSeek/OpenAI 的回答生成，忠实于检索上下文
- **评估体系**：20 条 ground truth，自动计算 Recall@5 和 Faithfulness

## 架构

```
数据采集 → 清洗 → 去重(MinHash) → 切分(800字/滑动窗口)
    → 向量化(bge-small-zh-v1.5) → 写入 FAISS

用户查询 → 查询分类 → 混合检索(FAISS+BM25) → 重排序 → LLM 生成回答
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 LLM API Key 和本地模型路径

# 3. 运行数据管线
python main.py pipeline --days 30 --limit 200

# 4. 启动 API 服务
python main.py serve --port 8001

# 5. 查询
curl -X POST http://localhost:8001/query -H "Content-Type: application/json" -d '{"query": "铜价走势"}'

# 6. 运行评估
python main.py eval
```

## 环境要求

- Python 3.10+
- 内存 8GB+（embedding batch_size 已针对低内存优化）
- Windows 需设置 `KMP_DUPLICATE_LIB_OK=TRUE` 和 `PYTORCH_NO_SHARED_MEMORY=1`（已内置）

## 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| Embedding | bge-small-zh-v1.5 | 512 维，中文优化，直接 transformers 调用 |
| 向量库 | FAISS | IndexIDMap + IndexFlatIP，余弦相似度 |
| 关键词检索 | rank_bm25 | BM25 算法 |
| 融合策略 | RRF | Reciprocal Rank Fusion |
| 去重 | MinHash + LSH | datasketch，阈值 0.85 |
| LLM | DeepSeek/OpenAI | OpenAI SDK 兼容格式 |
| API | FastAPI | `/query` POST 端点 |

## 项目结构

```
mini_rag/
├── main.py                 # CLI 入口
├── pipeline/
│   ├── sources/            # 数据采集（新闻/政策/价格）
│   ├── processors/         # 清洗/去重/切分
│   ├── embedder.py         # 向量化
│   ├── storage/            # FAISS 读写
│   └── run_pipeline.py     # 管线编排
├── serve/
│   ├── main.py             # FastAPI 服务
│   ├── retriever.py        # 混合检索
│   ├── generator.py        # LLM 回答生成
│   └── ...
├── eval/
│   ├── ground_truth.jsonl  # 20 条评估数据
│   └── run_eval.py         # 自动评估
└── DATA_NOTES.md           # 数据 Schema 说明
```
