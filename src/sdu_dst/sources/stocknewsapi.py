from __future__ import annotations

import os
import pandas as pd
from typing import Iterable

from .base import NewsSource
from ..api.client import ApiClient


class StockNewsAPISource(NewsSource):
    """
    Vendor-specific source for StockNewsAPI (BASIC tier).

    Covers:
    - Stock news
    - Company announcements / press-like news
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
    # 🔁 REQUIRED by NewsSource (compat wrapper)
    # -----------------------------------------------------
    async def fetch_events(
        self,
        query: str | None,
        start: str,
        end: str,
        **kwargs,
    ) -> pd.DataFrame:
        """
        StockNewsAPI does not support date-range queries in BASIC tier.
        This is a compatibility wrapper for the unified interface.
        """
        symbols = kwargs.get("symbols")
        limit = kwargs.get("limit", 10)

        if not symbols:
            return pd.DataFrame()

        return await self.fetch_stock_news(
            symbols=symbols,
            limit=limit,
        )

    # -----------------------------------------------------
    # 📰 Stock news / company news
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

        data = await self.client.get_json("", params=params)
        return self._to_df(data.get("data", []), "stock_news")

    # -----------------------------------------------------
    # 📣 Press-release-like company announcements
    # -----------------------------------------------------
    async def fetch_press_releases(
        self,
        symbols: Iterable[str],
        limit: int = 10,
    ) -> pd.DataFrame:
        return await self.fetch_stock_news(symbols, limit)

    # -----------------------------------------------------
    # 🔧 Mapper
    # -----------------------------------------------------
    def _to_df(self, items: list[dict], _: str) -> pd.DataFrame:
        rows = []

        for it in items:
            topics = it.get("topics", []) or []

            news_type = "press_release" if "PressRelease" in topics else "stock_news"

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
