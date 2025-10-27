from abc import ABC, abstractmethod
import pandas as pd
from typing import Iterable


class StockSource(ABC):
    @abstractmethod
    async def fetch_prices(
        self, symbols: Iterable[str], start: str, end: str, interval: str = "1d"
    ) -> pd.DataFrame:
        """Return price history in UTC"""


class NewsSource(ABC):
    @abstractmethod
    async def fetch_events(
        self, query: str | None, start: str, end: str, **kwargs
    ) -> pd.DataFrame:
        """Return events with UTC timestamps"""
