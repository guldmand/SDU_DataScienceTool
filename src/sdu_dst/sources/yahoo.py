from __future__ import annotations
import asyncio
import pandas as pd
import yfinance as yf
from typing import Iterable
from .base import StockSource


class YahooFinanceSource(StockSource):
    async def fetch_prices(
        self, symbols: Iterable[str], start: str, end: str, interval: str = "1d"
    ) -> pd.DataFrame:
        # yfinance er synkron; kør i thread pool for ikke at blokere event loop
        syms = list(symbols)

        def _dl():
            return yf.download(
                " ".join(syms),
                start=start,
                end=end,
                interval=interval,
                auto_adjust=False,
                group_by="ticker",
                progress=False,
            )

        df = await asyncio.to_thread(_dl)
        # Normaliser til MultiIndex (symbol, field) og UTC
        if isinstance(df.columns, pd.MultiIndex):
            pass
        else:
            df = pd.concat({syms[0]: df}, axis=1)
        df.index = pd.to_datetime(df.index, utc=True)
        return df
