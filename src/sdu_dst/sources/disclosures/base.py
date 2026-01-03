from abc import ABC, abstractmethod
import pandas as pd


class DisclosureSource(ABC):
    @abstractmethod
    async def fetch_company_disclosures(
        self,
        identifier: str,
        limit: int = 50,
    ) -> pd.DataFrame:
        """
        Fetch official company disclosures / press releases
        with UTC timestamps.
        """
