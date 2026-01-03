import asyncio
from sdu_dst.sources.stocknewsapi import StockNewsAPISource


async def main():
    src = StockNewsAPISource()

    df = await src.fetch_stock_news(
        symbols=["AAPL", "MSFT"],
        limit=5,
    )
    print(df)

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
