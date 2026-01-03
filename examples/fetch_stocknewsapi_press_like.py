import asyncio
from sdu_dst.sources.stocknewsapi import StockNewsAPISource


async def main():
    src = StockNewsAPISource()

    # Press-release-lignende nyheder (StockNewsAPI har ikke separat endpoint)
    df = await src.fetch_press_releases(
        symbols=["AAPL"],
        limit=5,
    )
    print(df)

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
