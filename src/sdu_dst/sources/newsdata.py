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
    - Market / company news
    - Press releases (datatype=press_release)

    Notes:
    - FREE tier has 12h delay
    - Limited request volume
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
        Required by NewsSource ABC.

        NewsData FREE tier does not support exact date filtering,
        so start/end are accepted but not enforced server-side.
        """
        limit = kwargs.get("limit", 10)

        return await self.fetch_news(
            query=query,
            limit=limit,
        )

    # -----------------------------------------------------
    # 📰 General / market / company news
    # -----------------------------------------------------
    async def fetch_news(
        self,
        query: Optional[str] = None,
        symbols: Optional[Iterable[str]] = None,
        datatype: Optional[str] = None,
        limit: int = 10,
    ) -> pd.DataFrame:
        params = {
            "apikey": self.api_key,
            "size": min(limit, 50),
        }

        if query:
            params["q"] = query

        if symbols:
            params["symbol"] = ",".join(symbols)

        if datatype:
            params["datatype"] = datatype  # news | press_release | blog | etc.

        data = await self.client.get_json("latest", params=params)
        return self._to_df(data.get("results", []), datatype or "news")

    # -----------------------------------------------------
    # 📣 Press releases (FREE-tier fallback)
    # -----------------------------------------------------
    async def fetch_press_releases(
        self,
        symbols: Optional[Iterable[str]] = None,
        limit: int = 10,
    ) -> pd.DataFrame:
        """
        NewsData.io FREE tier does NOT support symbol-filtered press releases.

        This method therefore:
        - Attempts press_release fetch WITHOUT symbol filtering
        - Falls back to empty DataFrame if API rejects request
        """
        try:
            return await self.fetch_news(
                datatype="press_release",
                limit=limit,
            )
        except Exception:
            # API returns 422 on unsupported combinations
            return pd.DataFrame(
                columns=[
                    "ts",
                    "headline",
                    "text",
                    "publisher",
                    "source",
                    "url",
                    "symbol",
                    "image",
                    "site",
                    "type",
                ]
            )

    # -----------------------------------------------------
    # 🔧 Mapper
    # -----------------------------------------------------
    def _to_df(self, items: list[dict], news_type: str) -> pd.DataFrame:
        rows = []
        for it in items:
            rows.append(
                {
                    "ts": pd.to_datetime(it.get("pubDate"), utc=True, errors="coerce"),
                    "headline": it.get("title"),
                    "text": it.get("description"),
                    "publisher": it.get("source_id"),
                    "source": "newsdata.io",
                    "url": it.get("link"),
                    "symbol": (
                        ",".join(it["symbol"])
                        if isinstance(it.get("symbol"), list)
                        else it.get("symbol")
                    ),
                    "image": it.get("image_url"),
                    "site": it.get("source_url"),
                    "type": news_type,
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.dropna(subset=["ts"]).sort_values("ts")

        return df
