from sdu_dst.sources.gdelt import GDELTSource
import asyncio


async def main():
    g = GDELTSource()
    events = await g.fetch_events("Apple", "2024-01-01", "2024-01-31")
    print(events.head())


asyncio.run(main())
