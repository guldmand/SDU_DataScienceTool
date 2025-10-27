import asyncio
from sdu_dst.sources.yahoo import YahooFinanceSource
from sdu_dst.sources.gdelt import GDELTSource


async def main():
    y = YahooFinanceSource()
    g = GDELTSource()

    prices = await y.fetch_prices(
        ["AAPL", "MSFT"], start="2021-01-01", end="2021-06-30"
    )
    print("Prices shape:", prices.shape)
    events = await g.fetch_events(query="Apple", start="2021-01-01", end="2021-06-30")
    print("Events rows:", len(events))
    print(events.head(3))

    await g.close()


if __name__ == "__main__":
    asyncio.run(main())
