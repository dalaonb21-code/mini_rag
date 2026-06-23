import feedparser, requests, time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from .base import BaseCrawler, RawDocument

RSS_URLS = [
    "https://www.mining.com/feed/",
    "https://www.mining.com/category/mining/feed/",
]

class NewsCrawler(BaseCrawler):
    def fetch(self) -> list[RawDocument]:
        docs, seen = [], set()
        cutoff = datetime.utcnow() - timedelta(days=self.days)

        for rss_url in RSS_URLS:
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