import asyncio
import argparse
from datetime import date
from sdu_dst.sources.gdelt import GDELTSource


async def main(query: str, start: str, end: str, maxrecords: int):
    src = GDELTSource()
    # NB: GDELTSource.fetch_events bruger p.t. ArtList og maxrecords=250 som default.
    # Vi kan styre antallet ved at passe det som parameter i en udvidelse; her holder vi basic.
    df = await src.fetch_events(query=query, start=start, end=end)
    if maxrecords and len(df) > maxrecords:
        df = df.head(maxrecords)
    print(f"Fetched events for query='{query}' from {start} to {end}")
    print("Rows:", len(df))
    print(df.head(10))
    await src.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch news events via GDELTSource")
    parser.add_argument("--query", "-q", default="Apple", help="Free-text query")
    parser.add_argument("--start", default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument(
        "--end", default=str(date.today()), help="End date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--maxrecords", type=int, default=50, help="Trim output display to first N rows"
    )
    args = parser.parse_args()

    asyncio.run(main(args.query, args.start, args.end, args.maxrecords))
