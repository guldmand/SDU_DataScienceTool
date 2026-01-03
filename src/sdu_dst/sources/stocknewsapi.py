from __future__ import annotations

import os
import pandas as pd
from typing import Iterable, Optional

from .base import NewsSource
from ..api.client import ApiClient


class StockNewsAPISource(NewsSource):
    """
    Vendor-specific source for StockNewsAPI (BASIC plan).

    Covers:
    - Stock-specific news (ticker-based)
    - General market news
    - Sentiment & ranking
    - Press-release-like company announcements
    """

    BASE_URL = "https://stocknewsapi.com/api/v1"

    def __init__(self):
        api_key = os.getenv("STOCKNEWS_API_KEY")
        if not api_key:
            raise RuntimeError("Missing API key: export STOCKNEWS_API_KEY")

        self.api_key = api_key
        self.client = ApiClient(self.BASE_URL)

    async def close(self):
        await self.client.close()

    # ---------------------------------------------------------
    # 📰 Stock / ticker news
    # ---------------------------------------------------------
    async def fetch_stock_news(
        self,
        symbols: Iterable[str],
        limit: int = 20,
        sentiment: Optional[str] = None,
    ) -> pd.DataFrame:
        params = {
            "tickers": ",".join(symbols),
            "items": limit,
            "token": self.api_key,
        }

        if sentiment:
            params["sentiment"] = sentiment

        data = await self.client.get_json("category", params=params)
        return self._to_df(data.get("data", []), news_type="stocknewsapi_stock")

    # ---------------------------------------------------------
    # 🌍 General market news
    # ---------------------------------------------------------
    async def fetch_general_news(self, limit: int = 20) -> pd.DataFrame:
        params = {
            "items": limit,
            "token": self.api_key,
        }

        data = await self.client.get_json("category", params=params)
        return self._to_df(data.get("data", []), news_type="stocknewsapi_general")

    # ---------------------------------------------------------
    # 📣 Press-release-like company news
    # ---------------------------------------------------------
    async def fetch_company_announcements(
        self, symbols: Iterable[str], limit: int = 20
    ) -> pd.DataFrame:
        params = {
            "tickers": ",".join(symbols),
            "items": limit,
            "token": self.api_key,
        }

        data = await self.client.get_json("category", params=params)
        return self._to_df(data.get("data", []), news_type="stocknewsapi_press_like")

    # ---------------------------------------------------------
    # 🔧 Intern helper
    # ---------------------------------------------------------
    def _to_df(self, data: list[dict], news_type: str) -> pd.DataFrame:
        rows = []
        for item in data:
            rows.append(
                {
                    "ts": pd.to_datetime(item.get("date"), utc=True, errors="coerce"),
                    "headline": item.get("title"),
                    "text": item.get("text"),
                    "source": "stocknewsapi",
                    "publisher": item.get("source_name"),
                    "url": item.get("news_url"),
                    "symbol": item.get("tickers"),
                    "sentiment": item.get("sentiment"),
                    "type": news_type,
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.dropna(subset=["ts"]).sort_values("ts")

        return df
