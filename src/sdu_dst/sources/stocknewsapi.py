from __future__ import annotations

import os
import pandas as pd
from typing import Iterable

from .base import NewsSource
from ..api.client import ApiClient


class StockNewsAPISource(NewsSource):
    """
    Vendor-specific source for StockNewsAPI (BASIC plan).

    Covers:
    - Stock / market news
    - Company-related news

    Notes:
    - No true press releases (PRs are mixed into stock news)
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

    # -----------------------------------------------------
    # 📰 Stock / market news
    # -----------------------------------------------------
    async def fetch_stock_news(
        self,
        symbols: Iterable[str],
        limit: int = 10,
    ) -> pd.DataFrame:
        params = {
            "tickers": ",".join(symbols),
            "items": limit,
            "token": self.api_key,
        }

        # Root endpoint: /api/v1
        data = await self.client.get_json("", params=params)
        return self._to_df(data.get("data", []), news_type="stock_news")

    # -----------------------------------------------------
    # 📣 Press releases (NOT distinct on this API)
    # -----------------------------------------------------
    async def fetch_press_releases(
        self,
        symbols: Iterable[str],
        limit: int = 10,
    ) -> pd.DataFrame:
        # StockNewsAPI does not separate PRs
        return await self.fetch_stock_news(symbols, limit)

    # -----------------------------------------------------
    # 🔧 Mapper
    # -----------------------------------------------------
    def _to_df(self, items: list[dict], news_type: str) -> pd.DataFrame:
        rows = []
        for it in items:
            rows.append(
                {
                    "ts": pd.to_datetime(it.get("date"), utc=True, errors="coerce"),
                    "headline": it.get("title"),
                    "text": it.get("text"),
                    "publisher": it.get("source_name"),
                    "source": "stocknewsapi",
                    "url": it.get("news_url"),
                    "symbol": (
                        ",".join(it["tickers"])
                        if isinstance(it.get("tickers"), list)
                        else it.get("tickers")
                    ),
                    "image": it.get("image_url"),
                    "site": it.get("source_name"),
                    "type": news_type,
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.dropna(subset=["ts"]).sort_values("ts")

        return df
