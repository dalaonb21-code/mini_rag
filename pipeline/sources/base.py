from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class RawDocument:
    source_type: str          # "news" | "policy" | "price"
    url: str
    title: str
    content: str
    published_at: Optional[datetime] = None
    extra: dict = field(default_factory=dict)   # 价格数据等结构化字段

class BaseCrawler(ABC):
    def __init__(self, days: int = 30, limit: int = 200):
        self.days = days
        self.limit = limit

    @abstractmethod
    def fetch(self) -> list[RawDocument]:
        """子类实现，返回 RawDocument 列表"""
        ...