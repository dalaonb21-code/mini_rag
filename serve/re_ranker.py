import os
from openai import OpenAI


class Reranker:
    """
    LLM-based reranker：让模型对候选文档打分，按得分重排。
    降级方案：若 LLM 不可用，直接返回原顺序。
    """

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-xxx"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def rerank(self, query: str, hits: list[dict], top_k: int = 5) -> list[dict]:
        if not hits:
            return []
        try:
            return self._llm_rerank(query, hits, top_k)
        except Exception:
            return hits[:top_k]

    def _llm_rerank(self, query: str, hits: list[dict], top_k: int) -> list[dict]:
        doc_list = "\n".join(
            f"[{i}] {h['title']}: {h['content'][:120]}" for i, h in enumerate(hits)
        )
        prompt = f"""对以下检索结果按与查询的相关性打分（0-10），返回JSON数组。
查询：{query}
文档：
{doc_list}

返回格式：[{{"idx": 0, "score": 9}}, ...]，只返回JSON，不要其他内容。"""

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=512,
        )
        import json

        text = resp.choices[0].message.content.strip()
        # 提取 JSON
        if "[" in text:
            text = text[text.index("[") : text.rindex("]") + 1]
        scores = json.loads(text)
        scored = sorted(scores, key=lambda x: x["score"], reverse=True)[:top_k]
        return [hits[s["idx"]] for s in scored if s["idx"] < len(hits)]
