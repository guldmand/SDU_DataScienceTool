from __future__ import annotations

import os
import pandas as pd
from typing import Iterable, Literal, Dict, Any

from .base import NewsSource
from ..api.client import ApiClient


class FinancialModelingPrepSource(NewsSource):
    """
    Vendor-specific source for Financial Modeling Prep (FMP).

    Covers:
    - Stock news
    - General news
    - Press releases (company announcements)
    - Company profile
    - Key metrics (TTM)
    - Financial statements (quarter / annual)
    """

    BASE_URL = "https://financialmodelingprep.com/stable"

    def __init__(self):
        api_key = os.getenv("FMP_API_KEY")
        if not api_key:
            raise RuntimeError("Missing API key: export FMP_API_KEY")

        self.api_key = api_key
        self.client = ApiClient(self.BASE_URL)

    async def close(self):
        await self.client.close()

    # ------------------------------------------------------------------
    # 📰 BACKWARD COMPAT (bruges af ældre examples / pipelines)
    # ------------------------------------------------------------------
    async def fetch_events(self, symbols: Iterable[str], **kwargs) -> pd.DataFrame:
        """
        Compatibility wrapper.
        Equivalent to fetch_stock_news.
        """
        return await self.fetch_stock_news(
            symbols=symbols,
            start=kwargs.get("start"),
            end=kwargs.get("end"),
        )

    # ------------------------------------------------------------------
    # 📰 Stock news (ticker-baseret)
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # 📰 Stock news – FULL HISTORY with paging + from/to
    # ------------------------------------------------------------------
    async def fetch_stock_news(
        self,
        symbols: Iterable[str],
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        Fetch ALL stock news for given symbols between start/end.
        Uses FMP paging (limit + page).
        """

        MAX_LIMIT = 250
        MAX_PAGES = 100

        all_rows = []

        start_dt = pd.to_datetime(start, utc=True) if start else None

        for page in range(MAX_PAGES):
            params = {
                "symbols": ",".join(symbols),
                "limit": MAX_LIMIT,
                "page": page,
                "apikey": self.api_key,
            }

            if start:
                params["from"] = start
            if end:
                params["to"] = end

            data = await self.client.get_json("news/stock", params=params)

            if not data:
                break  # no more pages

            df = self._news_to_df(data, news_type="stock_news")

            if df.empty:
                break

            # Stop hvis vi er kommet længere tilbage end start
            if start_dt is not None:
                oldest = df["ts"].min()
                if pd.notna(oldest) and oldest < start_dt:
                    df = df[df["ts"] >= start_dt]
                    all_rows.append(df)
                    break

            all_rows.append(df)

        if not all_rows:
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

        return (
            pd.concat(all_rows)
            .drop_duplicates(subset=["ts", "headline", "url"])
            .sort_values("ts")
        )

    # ------------------------------------------------------------------
    # 🌍 Generelle nyheder (CNBC, Reuters, m.fl.)
    # ------------------------------------------------------------------
    async def fetch_general_news(self, limit: int = 20) -> pd.DataFrame:
        params = {
            "limit": limit,
            "apikey": self.api_key,
        }
        data = await self.client.get_json("news/general-latest", params=params)
        return self._news_to_df(data, news_type="general_news")

    # ------------------------------------------------------------------
    # 📣 Selskabsmeddelelser (press releases) Starter and premium
    # ------------------------------------------------------------------
    async def fetch_press_releases(self, symbols, limit=20):
        try:
            data = await self.client.get_json(
                "news/press-releases",
                params={
                    "symbols": ",".join(symbols),
                    "limit": limit,
                    "apikey": self.api_key,
                },
            )
            return self._news_to_df(data, news_type="press_release")

        except Exception as e:
            # Press releases ikke tilgængelige på denne plan
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

    # ------------------------------------------------------------------
    # 🏢 Firma-profil
    # ------------------------------------------------------------------
    async def fetch_company_profile(self, symbol: str) -> pd.DataFrame:
        params = {
            "symbol": symbol,
            "apikey": self.api_key,
        }
        data = await self.client.get_json("profile", params=params)
        return pd.DataFrame(data)

    # ------------------------------------------------------------------
    # 📈 Market quote (price, beta, shares, 52w range, etc.)
    # ------------------------------------------------------------------
    async def fetch_market_quote(self, symbol: str) -> pd.DataFrame:
        params = {
            "symbol": symbol,
            "apikey": self.api_key,
        }
        data = await self.client.get_json("quote", params=params)
        return pd.DataFrame(data)

    # ------------------------------------------------------------------
    # 📊 Nøgletal (TTM)
    # ------------------------------------------------------------------
    async def fetch_key_metrics(self, symbol: str) -> pd.DataFrame:
        params = {
            "symbol": symbol,
            "period": "ttm",
            "apikey": self.api_key,
        }
        data = await self.client.get_json("key-metrics-ttm", params=params)
        return pd.DataFrame(data)

    # ------------------------------------------------------------------
    # 📄 Regnskaber (Q1–Q4 / annual)
    # ------------------------------------------------------------------
    async def fetch_financials(
        self,
        symbol: str,
        period: Literal["quarter", "annual"] = "quarter",
        limit: int = 4,
    ) -> Dict[str, pd.DataFrame]:
        params = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "apikey": self.api_key,
        }

        income = await self.client.get_json("income-statement", params=params)
        balance = await self.client.get_json("balance-sheet-statement", params=params)
        cashflow = await self.client.get_json("cash-flow-statement", params=params)
        earnings = await self.client.get_json("earnings", params=params)

        return {
            "income_statement": pd.DataFrame(income),
            "balance_sheet": pd.DataFrame(balance),
            "cash_flow": pd.DataFrame(cashflow),
            "earnings": pd.DataFrame(earnings),
        }

    # ------------------------------------------------------------------
    # 🔧 Intern helper
    # ------------------------------------------------------------------
    def _news_to_df(self, data: list[dict], news_type: str) -> pd.DataFrame:
        rows = []
        for item in data:
            rows.append(
                {
                    "ts": pd.to_datetime(
                        item.get("publishedDate"), utc=True, errors="coerce"
                    ),
                    "headline": item.get("title"),
                    "text": item.get("text"),
                    "publisher": item.get("publisher"),
                    "source": "financialmodelingprep",
                    "url": item.get("url"),
                    "symbol": item.get("symbol"),
                    "image": item.get("image"),
                    "site": item.get("site"),
                    "type": news_type,
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.dropna(subset=["ts"]).sort_values("ts")

        return df

    # More Key Metrics Data

    async def fetch_ratios(self, symbol: str) -> pd.DataFrame:
        params = {
            "symbol": symbol,
            "apikey": self.api_key,
        }
        """
        Should give the following metrics:
        priceEarningsRatioTTM,
		pegRatioTTM,
		earningsPerShareTTM,
		returnOnEquityTTM,
		dividendYieldTTM
        """
        data = await self.client.get_json("ratios-ttm", params=params)
        return pd.DataFrame(data)

    async def fetch_income_statement(
        self,
        symbol: str,
        period: Literal["annual", "quarter"] = "annual",
        limit: int = 4,
    ) -> pd.DataFrame:
        """
        Should give the following metrics:
        revenue,
        grossProfit,
        operatingIncome,
        EBITDA,
        netIncome,
        margins (can be calculated)
        """
        params = {
            "symbol": symbol,
            "period": period,
            "limit": limit,
            "apikey": self.api_key,
        }
        data = await self.client.get_json("income-statement", params=params)
        return pd.DataFrame(data)

    async def fetch_market_profile(self, symbol: str) -> pd.DataFrame:
        """
        Should give the following metrics:
        price
        marketCap
        beta
        sharesOutstanding
        sector
        industry
        currency
        """
        return await self.fetch_company_profile(symbol)
