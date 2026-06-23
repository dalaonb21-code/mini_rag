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
        if len(docs) < self.limit:
            print(f"[WARN] 政策采集 {len(docs)} 条不足 {self.limit}，补充 mock 数据")
            docs.extend(self._mock_policy(self.limit - len(docs)))
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

    def _mock_policy(self, count: int = 200) -> list[RawDocument]:
        """政策 mock 数据（爬取失败时兜底）"""
        from datetime import datetime, timedelta
        items = [
            # 中国政策
            {"title": "中国稀土集团发布关于加强稀土开采总量控制的通知", "content": "中国稀土集团发布关于加强稀土开采总量控制的通知，要求各下属企业严格控制稀土开采总量，保护稀土资源。2025年稀土开采总量控制指标为21万吨，其中轻稀土18万吨，中重稀土3万吨。各企业须严格执行，不得超采。", "region": "CN", "org": "中国稀土集团"},
            {"title": "工信部发布稀土行业规范条件", "content": "工信部发布稀土行业规范条件，对稀土开采、冶炼、综合利用等环节提出更高要求。要求企业建立完善的环保设施，废水废气达标排放，固体废物安全处置。", "region": "CN", "org": "工信部"},
            {"title": "自然资源部发布2025年矿产资源储量统计", "content": "自然资源部发布2025年矿产资源储量统计报告。报告显示，我国稀土资源储量居世界第一，锂矿资源储量增长显著，铁矿石资源储量保持稳定。", "region": "CN", "org": "自然资源部"},
            {"title": "商务部调整稀土出口许可证管理", "content": "商务部发布公告，调整稀土出口许可证管理办法。新规要求稀土出口企业必须具备相应资质，出口量不得超过核定配额。此举旨在保护战略资源，促进稀土产业高质量发展。", "region": "CN", "org": "商务部"},
            {"title": "发改委发布战略性矿产资源发展规划", "content": "国家发改委发布《战略性矿产资源发展规划(2025-2030)》，将稀土、锂、钴、镍等列为战略性矿产。规划提出加强国内勘探、优化储备体系、推进国际合作三大任务。", "region": "CN", "org": "发改委"},
            {"title": "生态环境部加强矿山生态修复监管", "content": "生态环境部发布通知，要求各地加强矿山生态修复监管。新建矿山必须编制生态修复方案，历史遗留矿山要在2027年前完成修复。违规企业将被列入失信名单。", "region": "CN", "org": "生态环境部"},
            {"title": "财政部调整矿产资源税税率", "content": "财政部发布公告，调整矿产资源税税率。稀土资源税税率上调至12%，锂矿资源税税率上调至8%。新税率自2025年7月1日起执行。", "region": "CN", "org": "财政部"},
            {"title": "国资委推动央企矿产资源整合", "content": "国资委召开会议，推动中央企业矿产资源整合。要求中国五矿、中铝集团等央企加大矿产资源勘探开发力度，提升资源保障能力。", "region": "CN", "org": "国资委"},
            {"title": "科技部支持关键矿产提取技术研发", "content": "科技部发布重点研发计划，支持关键矿产提取技术研发。重点支持锂、钴、镍等矿产的高效提取和回收利用技术，项目最高资助5000万元。", "region": "CN", "org": "科技部"},
            {"title": "海关总署加强矿产品进出口监管", "content": "海关总署发布公告，加强矿产品进出口监管。要求所有矿产品出口必须提供原产地证明和质量检测报告，严防走私和偷逃税款。", "region": "CN", "org": "海关总署"},
            # 澳洲政策
            {"title": "澳洲DISR发布关键矿产战略更新", "content": "澳大利亚工业、科学与资源部(DISR)发布关键矿产战略更新，将锂、钴、稀土等列为优先矿种。新战略加强了出口审批流程，要求关键矿产出口须经审批，确保供应链安全。", "region": "AU", "org": "DISR"},
            {"title": "澳大利亚关键矿产出口管制新规", "content": "澳大利亚政府出台关键矿产出口管制新规，对锂、镍、钴等关键矿产实施出口许可制度。新规旨在保障国内供应安全，同时维护国际贸易秩序。", "region": "AU", "org": "DISR"},
            {"title": "澳洲矿业投资环境报告发布", "content": "澳大利亚工业部发布年度矿业投资环境报告，指出澳洲矿业投资环境持续优化，关键矿产项目获得重点支持。报告特别提到锂矿和稀土矿的投资前景。", "region": "AU", "org": "DISR"},
            {"title": "澳大利亚发布关键矿产技术路线图", "content": "澳大利亚政府发布关键矿产技术路线图，规划未来十年关键矿产产业发展方向。重点支持锂电池回收、稀土分离提纯等技术研发。", "region": "AU", "org": "DISR"},
            {"title": "澳洲加强外国投资矿产资源审查", "content": "澳大利亚外国投资审查委员会(FIRB)加强对外资投资矿产资源项目的审查。涉及关键矿产的投资项目必须经过国家安全审查。", "region": "AU", "org": "FIRB"},
            {"title": "西澳州政府支持锂矿项目开发", "content": "西澳州政府宣布支持5个锂矿项目开发，提供税收优惠和基础设施支持。预计这些项目将创造3000个就业岗位，年产值达50亿澳元。", "region": "AU", "org": "西澳州政府"},
            {"title": "澳大利亚与日本加强关键矿产合作", "content": "澳大利亚与日本签署关键矿产合作备忘录，加强在锂、钴、稀土等领域的合作。日本将投资澳洲矿产项目，确保供应链安全。", "region": "AU", "org": "DFAT"},
            {"title": "澳洲发布矿业劳工短缺应对方案", "content": "澳大利亚政府发布矿业劳工短缺应对方案，通过技术移民培训等措施缓解矿业劳动力紧张。预计未来五年矿业需新增10万名工人。", "region": "AU", "org": "DEWR"},
            {"title": "澳大利亚更新矿产资源勘探指南", "content": "澳大利亚地质调查局更新矿产资源勘探指南，简化勘探许可审批流程。新规将审批时间从12个月缩短至6个月。", "region": "AU", "org": "GA"},
            {"title": "澳洲推进矿业数字化转型", "content": "澳大利亚政府投资2亿澳元推进矿业数字化转型，支持无人驾驶、智能矿山等技术应用。目标是到2030年实现50%矿山数字化运营。", "region": "AU", "org": "DISR"},
        ]
        docs = []
        for i in range(count):
            t = items[i % len(items)]
            date = datetime.utcnow() - timedelta(days=i % 30)
            docs.append(RawDocument(
                source_type="policy",
                url=f"mock://policy/{i}",
                title=t["title"],
                content=t["content"],
                published_at=date,
                extra={"region": t["region"], "org": t["org"], "is_mock": True},
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
