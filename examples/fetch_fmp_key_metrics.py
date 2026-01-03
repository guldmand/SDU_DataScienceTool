import asyncio
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


async def main():
    src = FinancialModelingPrepSource()

    df = await src.fetch_key_metrics("AAPL")
    print(df)

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
