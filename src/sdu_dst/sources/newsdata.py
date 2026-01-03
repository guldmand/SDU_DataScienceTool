from __future__ import annotations

import os
import pandas as pd
from typing import Iterable, Optional

from .base import NewsSource
from ..api.client import ApiClient


class NewsDataSource(NewsSource):
    """
    Vendor-specific source for NewsData.io (FREE tier).

    Covers:
    - General news
    - Market news
    - Keyword-based search

    Limitations:
    - 12h delay
    - No true press releases
    """

    BASE_URL = "https://newsdata.io/api/1"

    def __init__(self):
        api_key = os.getenv("NEWSDATA_API_KEY")
        if not api_key:
            raise RuntimeError("Missing API key: export NEWSDATA_API_KEY")

        self.api_key = api_key
        self.client = ApiClient(self.BASE_URL)

    async def close(self):
        await self.client.close()

    # ---------------------------------------------------------
    # 🌍 General / Market news
    # ---------------------------------------------------------
    async def fetch_latest_news(
        self,
        query: Optional[str] = None,
        language: str = "en",
        limit: int = 20,
    ) -> pd.DataFrame:
        params = {
            "apikey": self.api_key,
            "language": language,
            "size": limit,
        }

        if query:
            params["q"] = query

        data = await self.client.get_json("news", params=params)
        articles = data.get("results", [])

        return self._to_df(articles, news_type="newsdata_latest")

    # ---------------------------------------------------------
    # 🔧 Intern helper
    # ---------------------------------------------------------
    def _to_df(self, data: list[dict], news_type: str) -> pd.DataFrame:
        rows = []
        for item in data:
            rows.append(
                {
                    "ts": pd.to_datetime(
                        item.get("pubDate"), utc=True, errors="coerce"
                    ),
                    "headline": item.get("title"),
                    "text": item.get("description"),
                    "source": "newsdata.io",
                    "publisher": item.get("source_id"),
                    "url": item.get("link"),
                    "symbol": None,
                    "category": item.get("category"),
                    "country": item.get("country"),
                    "type": news_type,
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.dropna(subset=["ts"]).sort_values("ts")

        return df
