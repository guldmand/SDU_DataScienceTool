from __future__ import annotations
import pandas as pd
from ..api.client import ApiClient
from .base import NewsSource


class GDELTSource(NewsSource):
    def __init__(self) -> None:
        self.client = ApiClient("https://api.gdeltproject.org/api/v2")

    async def close(self):  # valgfri
        await self.client.close()

    async def fetch_events(
        self, query: str | None, start: str, end: str, mode: str = "eventcount"
    ) -> pd.DataFrame:
        # Simpelt ArtList eksempel
        params = {
            "query": query or "",
            "mode": "ArtList",
            "maxrecords": 250,
            "format": "json",
        }
        data = await self.client.get_json("doc/doc", params=params)
        # Normalisér til DataFrame (robusthed: GDELTs schema kan variere)
        rows = []
        if isinstance(data, dict) and "articles" in data:
            for a in data["articles"]:
                rows.append(
                    {
                        "ts": pd.to_datetime(
                            a.get("seendate"), utc=True, errors="coerce"
                        ),
                        "headline": a.get("title"),
                        "source": a.get("source"),
                        "url": a.get("url"),
                        # placeholders (kan mappes fra a.get("domain","lang","location") osv.)
                        "category": None,
                        "level": None,
                        "country": None,
                        "continent": None,
                        "tickers": [],
                    }
                )
        df = pd.DataFrame(rows).dropna(subset=["ts"])
        return df
