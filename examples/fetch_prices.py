import asyncio
import argparse
from datetime import date
from sdu_dst.sources.yahoo import YahooFinanceSource


async def main(symbols: list[str], start: str, end: str, interval: str):
    src = YahooFinanceSource()
    df = await src.fetch_prices(symbols, start=start, end=end, interval=interval)
    print(f"Fetched prices for {symbols} from {start} to {end} (interval={interval})")
    print("Shape:", df.shape)
    print(df.head())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch historical prices via YahooFinanceSource"
    )
    parser.add_argument(
        "--symbols",
        "-s",
        nargs="+",
        default=["AAPL"],
        help="Ticker symbols (space separated)",
    )
    parser.add_argument("--start", default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument(
        "--end", default=str(date.today()), help="End date (YYYY-MM-DD)"
    )
    parser.add_argument("--interval", default="1d", help="Interval (e.g. 1d, 1wk, 1mo)")
    args = parser.parse_args()

    asyncio.run(main(args.symbols, args.start, args.end, args.interval))
