import asyncio
from sdu_dst.sources.financialmodelingprep import FinancialModelingPrepSource


async def main():
    src = FinancialModelingPrepSource()

    df = await src.fetch_press_releases(["AAPL"], limit=5)
    print(df)

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
