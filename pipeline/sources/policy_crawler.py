import requests, time, re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseCrawler, RawDocument

SOURCES = [
    {
        "name": "china_rare_earth",
        "base_url": "https://www.cregroup.com.cn",
        "list_url": "https://www.cregroup.com.cn/xwzx/index.jhtml",  # 新闻中心
        "type": "list",
    },
    {
        "name": "au_disr",
        "base_url": "https://www.industry.gov.au",
        "list_url": "https://www.industry.gov.au/publications",
        "type": "list",
    },
]


class PolicyCrawler(BaseCrawler):
    """政策爬虫：中国稀土集团 + 澳洲 DISR"""

    def fetch(self) -> list[RawDocument]:
        docs: list[RawDocument] = []
        docs.extend(self._crawl_china_rare_earth())
        docs.extend(self._crawl_au_disr())
        if len(docs) < 10:
            print("[WARN] 政策爬取不足，补充 mock 数据")
            docs.extend(self._mock_policy())
        return docs[: self.limit]

    # ---- 中国稀土集团 ----
    def _crawl_china_rare_earth(self) -> list[RawDocument]:
        docs: list[RawDocument] = []
        cutoff = datetime.utcnow() - timedelta(days=self.days)
        try:
            resp = requests.get(
                SOURCES[0]["list_url"],
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a[href]")
            for a in links:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or len(title) < 6:
                    continue
                if not href.startswith("http"):
                    href = SOURCES[0]["base_url"] + href
                if "/xwzx/" not in href and "/gsgg/" not in href:
                    continue
                content = self._fetch_page_text(href)
                if len(content) < 80:
                    continue
                docs.append(
                    RawDocument(
                        source_type="policy",
                        url=href,
                        title=title,
                        content=content,
                        published_at=datetime.utcnow(),
                        extra={"region": "CN", "org": "中国稀土集团"},
                    )
                )
                if len(docs) >= self.limit // 2:
                    break
                time.sleep(1.5)
        except Exception as e:
            print(f"[WARN] china_rare_earth crawl failed: {e}")
        return docs

    # ---- 澳洲 DISR ----
    def _crawl_au_disr(self) -> list[RawDocument]:
        docs: list[RawDocument] = []
        try:
            resp = requests.get(
                SOURCES[1]["list_url"],
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15,
            )
            soup = BeautifulSoup(resp.text, "html.parser")
            links = soup.select("a[href*='publication'], a[href*='critical-mineral']")
            for a in links:
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or len(title) < 8:
                    continue
                if not href.startswith("http"):
                    href = SOURCES[1]["base_url"] + href
                content = self._fetch_page_text(href)
                if len(content) < 80:
                    continue
                docs.append(
                    RawDocument(
                        source_type="policy",
                        url=href,
                        title=title,
                        content=content,
                        published_at=datetime.utcnow(),
                        extra={"region": "AU", "org": "DISR"},
                    )
                )
                if len(docs) >= self.limit // 2:
                    break
                time.sleep(1.5)
        except Exception as e:
            print(f"[WARN] au_disr crawl failed: {e}")
        return docs

    def _mock_policy(self) -> list[RawDocument]:
        """政策 mock 数据（爬取失败时兜底）"""
        from datetime import datetime, timedelta
        items = [
            {"title": "中国稀土集团发布关于加强稀土开采总量控制的通知", "content": "中国稀土集团发布关于加强稀土开采总量控制的通知，要求各下属企业严格控制稀土开采总量，保护稀土资源。2025年稀土开采总量控制指标为21万吨，其中轻稀土18万吨，中重稀土3万吨。各企业须严格执行，不得超采。", "region": "CN", "org": "中国稀土集团"},
            {"title": "澳洲DISR发布关键矿产战略更新", "content": "澳大利亚工业、科学与资源部(DISR)发布关键矿产战略更新，将锂、钴、稀土等列为优先矿种。新战略加强了出口审批流程，要求关键矿产出口须经审批，确保供应链安全。", "region": "AU", "org": "DISR"},
            {"title": "工信部发布稀土行业规范条件", "content": "工信部发布稀土行业规范条件，对稀土开采、冶炼、综合利用等环节提出更高要求。要求企业建立完善的环保设施，废水废气达标排放，固体废物安全处置。", "region": "CN", "org": "工信部"},
            {"title": "澳大利亚关键矿产出口管制新规", "content": "澳大利亚政府出台关键矿产出口管制新规，对锂、镍、钴等关键矿产实施出口许可制度。新规旨在保障国内供应安全，同时维护国际贸易秩序。", "region": "AU", "org": "DISR"},
            {"title": "自然资源部发布2025年矿产资源储量统计", "content": "自然资源部发布2025年矿产资源储量统计报告。报告显示，我国稀土资源储量居世界第一，锂矿资源储量增长显著，铁矿石资源储量保持稳定。", "region": "CN", "org": "自然资源部"},
            {"title": "澳洲矿业投资环境报告发布", "content": "澳大利亚工业部发布年度矿业投资环境报告，指出澳洲矿业投资环境持续优化，关键矿产项目获得重点支持。报告特别提到锂矿和稀土矿的投资前景。", "region": "AU", "org": "DISR"},
        ]
        docs = []
        for i, item in enumerate(items):
            date = datetime.utcnow() - timedelta(days=i)
            docs.append(RawDocument(
                source_type="policy",
                url=f"mock://policy/{i}",
                title=item["title"],
                content=item["content"],
                published_at=date,
                extra={"region": item["region"], "org": item["org"]},
            ))
        return docs

    @staticmethod
    def _fetch_page_text(url: str) -> str:
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            article = soup.select_one(
                ".article-content, .content, article, main, .entry-content, .field-item"
            )
            text = article.get_text(separator="\n", strip=True) if article else soup.get_text(separator="\n", strip=True)
            return re.sub(r"\n{3,}", "\n\n", text)[:4000]
        except Exception:
            return ""
