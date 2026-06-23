import requests
from datetime import datetime, timedelta
from .base import BaseCrawler, RawDocument


class PriceFetcher(BaseCrawler):
    """
    价格数据源：LME 铜锌镍 + SHFE 锂 + 上海钢联铁矿石
    优先公开接口；登录墙/频控降级为 mock 数据。
    """

    LME_METALS = ["copper", "zinc", "nickel"]

    def fetch(self) -> list[RawDocument]:
        docs: list[RawDocument] = []
        # LME 铜锌镍
        for metal in self.LME_METALS:
            try:
                docs.extend(self._fetch_lme(metal))
            except Exception as e:
                print(f"[WARN] LME {metal} fetch failed: {e}, using mock")
                docs.extend(self._mock_lme(metal))
        # SHFE 碳酸锂
        docs.extend(self._mock_shfe_lithium())
        # 上海钢联 铁矿石
        docs.extend(self._mock_iron_ore())
        return docs[: self.limit]

    # ---- LME ----
    def _fetch_lme(self, metal: str) -> list[RawDocument]:
        import os

        api_key = os.getenv("METALS_API_KEY", "")
        if not api_key:
            return self._mock_lme(metal)

        resp = requests.get(
            "https://metals-api.com/api/latest",
            params={"access_key": api_key, "base": "USD", "symbols": metal.upper()},
            timeout=10,
        )
        data = resp.json()
        price = data["rates"].get(metal.upper(), 0)
        content = f"{metal.upper()} 最新LME现货价格：{price} USD/t（{datetime.utcnow().date()}）。LME {metal}价格受全球供需、美元汇率及宏观经济影响。"
        return [
            RawDocument(
                source_type="price",
                url=f"https://metals-api.com/{metal}",
                title=f"LME {metal.upper()} 价格",
                content=content,
                published_at=datetime.utcnow(),
                extra={"metal": metal, "price": price, "currency": "USD", "exchange": "LME"},
            )
        ]

    def _mock_lme(self, metal: str) -> list[RawDocument]:
        """LME 30天 mock 价格"""
        base_prices = {"copper": 9800, "zinc": 2700, "nickel": 18000}
        docs = []
        base = base_prices.get(metal, 5000)
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            price = base + (i % 7 - 3) * 50
            content = f"[MOCK] {metal.upper()} LME现货价格 {date.date()}: {price} USD/t。近期{metal}价格在{base-150}-{base+150}美元/吨区间波动，受全球供需影响较大。"
            docs.append(
                RawDocument(
                    source_type="price",
                    url=f"mock://lme/{metal}/{date.date()}",
                    title=f"LME {metal.upper()} 价格 {date.date()}",
                    content=content,
                    published_at=date,
                    extra={"metal": metal, "price": price, "currency": "USD", "exchange": "LME", "is_mock": True},
                )
            )
        return docs

    # ---- SHFE 碳酸锂 ----
    def _mock_shfe_lithium(self) -> list[RawDocument]:
        """SHFE 碳酸锂 30天 mock（登录墙降级）"""
        docs = []
        base = 105000  # 元/吨
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            price = base + (i % 10 - 5) * 2000
            content = f"[MOCK] 碳酸锂期货 SHFE主力合约 {date.date()} 收盘价: {price} 元/吨。碳酸锂近期价格在100000-110000元/吨区间震荡，受新能源汽车需求和锂矿供应影响。"
            docs.append(
                RawDocument(
                    source_type="price",
                    url=f"mock://shfe/lithium/{date.date()}",
                    title=f"SHFE 碳酸锂 {date.date()}",
                    content=content,
                    published_at=date,
                    extra={"metal": "lithium", "price": price, "currency": "CNY", "exchange": "SHFE", "is_mock": True},
                )
            )
        return docs

    # ---- 上海钢联 铁矿石 ----
    def _mock_iron_ore(self) -> list[RawDocument]:
        """上海钢联铁矿石 30天 mock（接口频控降级）"""
        docs = []
        base = 850  # 元/吨，62%品位
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            price = base + (i % 8 - 4) * 15
            content = f"[MOCK] 铁矿石62%品位 上海钢联 {date.date()} 报价: {price} 元/湿吨。铁矿石价格近期在830-870元/湿吨区间波动，受钢铁需求和港口库存影响。"
            docs.append(
                RawDocument(
                    source_type="price",
                    url=f"mock://mysteel/iron_ore/{date.date()}",
                    title=f"铁矿石价格 {date.date()}",
                    content=content,
                    published_at=date,
                    extra={"metal": "iron_ore", "grade": "62%", "price": price, "currency": "CNY", "source": "上海钢联", "is_mock": True},
                )
            )
        return docs
