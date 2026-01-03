import asyncio
from sdu_dst.sources.newsdata import NewsDataSource


async def main():
    src = NewsDataSource()

    df = await src.fetch_press_releases(
        symbols=["AAPL"],
        limit=5,
    )
    print(df)

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
