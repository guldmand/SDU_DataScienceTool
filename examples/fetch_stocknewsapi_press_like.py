import asyncio
from sdu_dst.sources.stocknewsapi import StockNewsAPISource


async def main():
    src = StockNewsAPISource()

    df = await src.fetch_company_announcements(["AAPL"], limit=5)
    print(df)

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
