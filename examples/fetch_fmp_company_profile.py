import asyncio
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


async def main():
    src = FinancialModelingPrepSource()

    df = await src.fetch_company_profile("AAPL")
    print(df.T)  # transponeret = nemmere at læse

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
