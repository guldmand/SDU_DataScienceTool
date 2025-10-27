from __future__ import annotations
import asyncio, contextlib
import orjson
import websockets  # pip install websockets


async def stream(url: str, *, subscribe=None, heartbeat_sec: int = 20, reconnect=True):
    """
    WebSocket streaming generator:
    - auto-subscribe (fx {"type":"subscribe","symbol":"AAPL"})
    - ping/heartbeat
    - auto-reconnect (eksponentielt backoff)
    """
    backoff = 1
    while True:
        try:
            async with websockets.connect(url, ping_interval=heartbeat_sec) as ws:
                if subscribe is not None:
                    await ws.send(orjson.dumps(subscribe).decode())
                async for msg in ws:
                    yield orjson.loads(msg)
                backoff = 1  # reset if clean close
        except Exception:
            if not reconnect:
                raise
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
