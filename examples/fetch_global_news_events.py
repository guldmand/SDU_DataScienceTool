from sdu_dst.sources.gdelt import GDELTSource
import asyncio


async def main():
    src = GDELTSource()
    events = await src.fetch_events("Apple", "2024-01-01", "2024-01-31")
    print(events.head())
    await src.close()


asyncio.run(main())
