import os
from openai import OpenAI


SYSTEM_PROMPT = """你是矿业领域的 RAG 助手。根据提供的上下文回答用户问题。
规则：
1. 只基于上下文中的信息回答，不要编造。
2. 如果上下文没有相关信息，明确说"根据已有数据未找到相关信息"。
3. 回答用中文，简洁准确。
4. 引用来源时标注 [来源: 标题]。
"""


class Generator:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "sk-xxx"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def generate(self, query: str, hits: list[dict]) -> str:
        from .augmentor import build_context

        context = build_context(hits)
        user_msg = f"上下文：\n{context}\n\n问题：{query}"

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
                max_tokens=1024,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"[LLM 调用失败: {e}] 以下是检索到的相关内容：\n{context[:1000]}"
