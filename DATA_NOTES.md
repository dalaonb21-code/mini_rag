# Mining RAG — 数据说明

## 数据源概览

| # | 源 | 类型 | URL | 数据量目标 | 采集方式 |
|---|------|------|-----|-----------|---------|
| 1 | 矿业新闻 | news | mining.com RSS | ≥200条/30天 | RSS + 全文爬取 |
| 2 | 关键矿产政策 | policy | 中国稀土集团 / 澳洲DISR | ≥200条/30天 | HTML列表爬取 |
| 3 | 矿产价格 | price | LME/SHFE/上海钢联 | ≥200条/30天 | API + mock降级 |

## 向量库（FAISS）

使用 **FAISS IndexIDMap + IndexFlatIP**（归一化后内积 ≈ cosine similarity）。

### 文件布局

```
data/
├── faiss_index.bin    # FAISS 向量索引
└── metadata.json      # chunk 元数据（与 FAISS 行号对齐）
```

### 元数据 Schema（metadata.json 每条记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | sha256(url\|title)[:32] + chunk序号 |
| source_type | string | news / policy / price |
| title | string | 文档标题 |
| content | string | 文本内容（chunk），≤4000字符 |
| url | string | 原始URL |
| published_ts | int | 发布时间 Unix timestamp |

**索引类型**: IndexIDMap(IndexFlatIP), 向量维度 512 (bge-small-zh-v1.5), 内积度量（L2归一化后等价cosine）

## 主键生成规则

```
doc_id = sha256(url + "|" + title)[:32]
chunk_id = doc_id + "_" + chunk_index   # 长文档切分时
```

## 去重策略

使用 **MinHash + LSH** 进行近似去重：

1. 对每条文档的 `title + content[:200]` 生成 MinHash 签名
2. LSH 阈值 0.85（128 permutations）
3. 新文档先查询 LSH，命中则跳过，未命中则插入

去重粒度：URL 级别（同一 URL 不重复入库）+ 内容相似度（不同 URL 但内容高度相似也去重）

## 数据清洗

1. 去除 HTML 标签残留
2. 规范化空白字符
3. 截断到 4000 字符
4. 过滤 content < 50 字符的短文档

## Chunk 切分

- 短文档（≤800字符）：不切分，直接作为单 chunk
- 长文档：滑动窗口 800 字符，重叠 100 字符

## 价格数据降级说明

| 数据源 | 理想方案 | 降级方案 | 原因 |
|--------|---------|---------|------|
| LME 铜锌镍 | metals-api.com | 30天 mock 数据 | 需 API Key |
| SHFE 碳酸锂 | SHFE 官网 | 30天 mock 数据 | 登录墙 |
| 上海钢联铁矿石 | mysteel.com API | 30天 mock 数据 | 接口频控 |

Mock 数据格式与真实数据一致，`extra.is_mock = True` 标记。

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| OPENAI_API_KEY | LLM API Key | sk-xxx |
| OPENAI_BASE_URL | LLM API 地址 | https://api.openai.com/v1 |
| LLM_MODEL | LLM 模型名 | gpt-4o-mini |
| BGE_M3_PATH | Embedding 模型目录 | D:\Pycharm\mini_rag\model\bge-small-zh-v1.5 |
| METALS_API_KEY | metals-api.com Key | (空=降级mock) |
| FAISS_DATA_DIR | FAISS 数据目录 | data |
