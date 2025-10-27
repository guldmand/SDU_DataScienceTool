from __future__ import annotations
import contextlib, hashlib
import httpx
from aiolimiter import AsyncLimiter
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from cachetools import TTLCache
import orjson

try:
    import uvloop
    uvloop.install()
except Exception:
    pass

with contextlib.suppress(Exception):
    import redis
    _redis = redis.Redis(host="localhost", port=6379, decode_responses=False)
else:
    _redis = None

class ApiClient:
    """
    Async HTTP client supporting:
    - HTTP/2 connection pooling
    - Rate limiting
    - Retries with exponential backoff
    - Redis or memory TTL cache
    """
    def __init__(self, base_url: str = "", *, rps: int = 10, timeout_s: float = 10.0,
                 cache_ttl_s: int = 60, headers: dict | None = None):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(http2=True, timeout=timeout_s, headers=headers or {})
        self.limiter = AsyncLimiter(rps, time_period=1)
        self.cache = TTLCache(maxsize=10_000, ttl=cache_ttl_s)
        self.cache_ttl_s = cache_ttl_s

    async def close(self) -> None:
        await self.client.aclose()

    def _mkurl(self, path: str) -> str:
        return path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"

    @staticmethod
    def _key(method: str, url: str, params: dict | None) -> bytes:
        raw = orjson.dumps({"m": method, "u": url, "p": params or {} })
        return hashlib.blake2b(raw, digest_size=16).digest()

    async def _cache_get(self, key: bytes):
        if _redis:
            val = _redis.get(key)
            if val:
                return orjson.loads(val)
        return self.cache.get(key)

    async def _cache_set(self, key: bytes, value) -> None:
        data = orjson.dumps(value)
        if _redis:
            _redis.setex(key, self.cache_ttl_s, data)
        else:
            self.cache[key] = value

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=3.0),
        retry=retry_if_exception_type((httpx.TransportError, httpx.ReadTimeout)),
    )
    async def _request(self, method: str, url: str, *, params=None, json=None, headers=None, use_cache=True):
        async with self.limiter:
            ck = self._key(method, url, params)
            if use_cache:
                cached = await self._cache_get(ck)
                if cached is not None:
                    return cached
            resp = await self.client.request(method, url, params=params, json=json, headers=headers)
            resp.raise_for_status()
            is_json = "application/json" in resp.headers.get("content-type", "")
            data = resp.json(loads=orjson.loads) if is_json else resp.text
            if use_cache:
                await self._cache_set(ck, data)
            return data

    async def get_json(self, path: str, *, params=None, headers=None, use_cache=True):
        return await self._request("GET", self._mkurl(path), params=params, headers=headers, use_cache=use_cache)

    async def post_json(self, path: str, *, payload=None, headers=None, use_cache=False):
        return await self._request("POST", self._mkurl(path), json=payload, headers=headers, use_cache=use_cache)
