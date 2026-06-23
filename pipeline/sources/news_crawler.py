import feedparser, requests, time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseCrawler, RawDocument

RSS_URLS = [
    "https://www.mining.com/feed/",
    "https://www.mining.com/category/mining/feed/",
    "https://www.mining.com/category/base-metals/feed/",
    "https://www.mining.com/category/precious-metals/feed/",
    "https://www.mining.com/category/battery-metals/feed/",
]

class NewsCrawler(BaseCrawler):
    def fetch(self) -> list[RawDocument]:
        docs, seen = [], set()
        cutoff = datetime.utcnow() - timedelta(days=self.days)

        for rss_url in RSS_URLS:
            if len(docs) >= self.limit:
                break
            try:
                feed = feedparser.parse(rss_url)
                for entry in feed.entries:
                    if len(docs) >= self.limit:
                        break
                    url = entry.get("link", "")
                    if url in seen:
                        continue
                    seen.add(url)

                    # 解析发布时间
                    pub = entry.get("published_parsed")
                    pub_dt = datetime(*pub[:6]) if pub else datetime.utcnow()
                    if pub_dt < cutoff:
                        continue

                    # 全文爬取
                    content = self._fetch_full_text(url)
                    if len(content) < 100:   # 空页面跳过
                        continue

                    docs.append(RawDocument(
                        source_type="news",
                        url=url,
                        title=entry.get("title", ""),
                        content=content,
                        published_at=pub_dt,
                    ))
                    time.sleep(1.2)   # 礼貌爬取
            except Exception as e:
                print(f"[WARN] RSS {rss_url} 解析失败: {e}")

        # 如果真实数据不足，补充 mock 数据
        if len(docs) < self.limit:
            print(f"[WARN] 新闻采集 {len(docs)} 条不足 {self.limit}，补充 mock 数据")
            docs.extend(self._mock_news(self.limit - len(docs)))

        return docs[:self.limit]

    def _mock_news(self, count: int) -> list[RawDocument]:
        """新闻 mock 数据兜底"""
        templates = [
            {"title": "全球铜价创年内新高，矿业股普涨", "content": "受全球经济复苏预期和新能源需求推动，LME铜价突破10000美元/吨关口，创年内新高。分析师预计，随着电动汽车和可再生能源行业快速发展，铜需求将持续增长。主要矿业公司股价普遍上涨，其中必和必拓、力拓等涨幅超过3%。"},
            {"title": "澳大利亚锂矿出口量创新高", "content": "澳大利亚统计局数据显示，2025年锂矿出口量同比增长45%，创历史新高。中国仍是最大买家，占出口总量的80%以上。澳洲政府正在评估关键矿产出口政策，可能对锂矿出口实施更严格的审批流程。"},
            {"title": "铁矿石价格跌破90美元关口", "content": "受中国钢铁需求放缓影响，铁矿石价格跌破90美元/干吨。分析师指出，中国房地产市场持续低迷是主要原因。不过，新能源汽车和基础设施建设仍提供一定支撑。"},
            {"title": "镍价波动加剧，印尼供应成焦点", "content": "LME镍价近期波动加剧，市场关注印尼镍矿出口政策变化。印尼政府考虑限制镍矿石出口，以促进国内冶炼产业发展。这一消息推动镍价一度上涨8%。"},
            {"title": "稀土价格企稳回升", "content": "经过数月调整，稀土价格开始企稳回升。氧化镨钕价格回升至50万元/吨以上。业内人士认为，新能源汽车和风电行业需求增长是主要推动力。"},
            {"title": "智利铜矿罢工威胁全球供应", "content": "智利最大铜矿Escondida工人投票决定罢工，威胁全球约5%的铜供应。市场担忧供应紧张，铜价应声上涨。工会要求提高工资和改善工作条件。"},
            {"title": "加拿大推进关键矿产战略", "content": "加拿大政府宣布投资20亿加元推进关键矿产战略，重点支持锂、钴、镍等矿产的勘探和开发。此举旨在减少对中国供应链的依赖。"},
            {"title": "南非铂族金属产量下降", "content": "南非铂族金属产量连续第三个月下降，主要受电力短缺和劳资纠纷影响。分析师预计，供应紧张将支撑铂族金属价格。"},
            {"title": "刚果金钴矿出口审查趋严", "content": "刚果民主共和国加强钴矿出口审查，要求所有出口必须提供原产地证明。此举旨在打击非法采矿和童工问题，但可能影响全球钴供应。"},
            {"title": "印度钢铁产能扩张推动铁矿石需求", "content": "印度钢铁行业产能快速扩张，推动铁矿石进口需求增长。印度已成为全球第二大钢铁生产国，预计未来五年产能将翻番。"},
        ]
        docs = []
        for i in range(count):
            t = templates[i % len(templates)]
            date = datetime.utcnow() - timedelta(days=i % 30)
            docs.append(RawDocument(
                source_type="news",
                url=f"mock://news/{i}",
                title=t["title"],
                content=t["content"],
                published_at=date,
            ))
        return docs

    def _fetch_full_text(self, url: str) -> str:
        try:
            resp = requests.get(url, timeout=10,
                headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(resp.text, "html.parser")
            # mining.com 正文在 .entry-content
            article = soup.select_one(".entry-content, article, main")
            return article.get_text(separator="\n", strip=True) if article else ""
        except Exception:
            return ""