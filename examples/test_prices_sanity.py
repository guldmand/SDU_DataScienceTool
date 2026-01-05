import asyncio
from sdu_dst.sources.yahoo import YahooFinanceSource


async def main():
    src = YahooFinanceSource()

    symbol = "AAPL"

    print("Fetching prices for", symbol)

    df = await src.fetch_prices(
        symbol,
        period="1mo",
        interval="1d",
    )

    print(df.head())
    print()
    print("Rows:", len(df))

    await src.close()


if __name__ == "__main__":
    asyncio.run(main())
