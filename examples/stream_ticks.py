import asyncio
from sdu_dst.api.ws import stream


async def main():
    url = "wss://your-provider.example.com/stream"
    async for msg in stream(url, subscribe={"type": "subscribe", "symbol": "AAPL"}):
        print(msg)  # læg i asyncio.Queue i produktion


asyncio.run(main())
