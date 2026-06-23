def build_context(hits: list[dict], max_tokens: int = 3000) -> str:
    """
    将检索结果拼接为 LLM context，按相关度降序排列，
    控制总 token 数（粗略按 1 中文字 ≈ 2 token）。
    """
    parts = []
    total = 0
    for h in hits:
        snippet = f"[{h.get('source_type', '')}] {h['title']}\n{h['content']}"
        est_tokens = len(snippet) * 2
        if total + est_tokens > max_tokens:
            break
        parts.append(snippet)
        total += est_tokens
    return "\n\n---\n\n".join(parts)
