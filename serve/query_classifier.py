import re


def classify_query(query: str) -> str:
    """
    基于关键词的查询分类：news / policy / price
    用于过滤 source_type 字段
    """
    q = query.lower()

    price_kw = [
        "价格", "价", "行情", "涨", "跌", "报价", "美元", "usd", "lme", "shfe",
        "铜", "锌", "镍", "锂", "铁矿", "碳酸锂", "期货", "现货",
        "price", "quotation", "spot", "futures",
    ]
    policy_kw = [
        "政策", "法规", "条例", "战略", "规划", "出口管制", "稀土",
        "关税", "补贴", "审批", "许可", "战略矿产", "critical mineral",
        "strategy", "policy", "regulation", "export control",
    ]

    price_score = sum(1 for kw in price_kw if kw in q)
    policy_score = sum(1 for kw in policy_kw if kw in q)

    if price_score > policy_score:
        return "price"
    if policy_score > price_score:
        return "policy"
    return "news"
