from sdu_dst.sources.yahoo import YahooFinanceSource
import asyncio


async def main():
    y = YahooFinanceSource()
    df = await y.fetch_prices(["AAPL"], "2024-01-01", "2024-01-31")
    print(df.head())


asyncio.run(main())
