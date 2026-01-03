import asyncio
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


async def main():
    src = FinancialModelingPrepSource()

    financials = await src.fetch_financials(
        symbol="AAPL",
        period="quarter",
        limit=4,
    )

    print("\n=== Income Statement ===")
    print(financials["income_statement"].head())

    print("\n=== Balance Sheet ===")
    print(financials["balance_sheet"].head())

    print("\n=== Cash Flow ===")
    print(financials["cash_flow"].head())

    print("\n=== Earnings ===")
    print(financials["earnings"].head())

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
