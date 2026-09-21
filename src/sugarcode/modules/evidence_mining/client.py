"""Small, auditable clients for public biomedical evidence APIs.

Only the Python standard library is used. Responses are content-addressed by the
SHA-256 of the canonical request URL and response bytes are verified on reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import threading
import time
from typing import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class EvidenceAPIError(RuntimeError):
    """A public API request failed or returned malformed data."""


class OfflineCacheMiss(EvidenceAPIError):
    """Offline mode was requested but no verified cached response exists."""


Transport = Callable[[str, Mapping[str, str], float], bytes]


def _default_transport(url: str, headers: Mapping[str, str], timeout: float) -> bytes:
    try:
        with urlopen(Request(url, headers=dict(headers)), timeout=timeout) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise EvidenceAPIError(f"request failed for {url}: {exc}") from exc


@dataclass(frozen=True)
class CacheRecord:
    url: str
    fetched_at: float
    body_sha256: str


class CachedHTTPClient:
    """Throttled GET client with a tamper-evident disk cache.

    Offline mode never falls back to the network. Corrupt cache entries are
    rejected rather than interpreted as evidence.
    """

    def __init__(self, cache_dir: str | Path, *, min_interval: float = 0.34,
                 timeout: float = 20.0, user_agent: str = "sugarcode-ai/0.1 evidence-mining",
                 transport: Transport | None = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_interval = max(0.0, float(min_interval))
        self.timeout = float(timeout)
        self.headers = {"User-Agent": user_agent, "Accept": "application/json, application/xml"}
        self.transport = transport or _default_transport
        self._lock = threading.Lock()
        self._last_request = 0.0

    @staticmethod
    def canonical_url(base: str, params: Mapping[str, object] | None = None) -> str:
        pairs = [(str(k), str(v)) for k, v in (params or {}).items() if v is not None]
        return base + (("&" if "?" in base else "?") + urlencode(sorted(pairs)) if pairs else "")

    def get(self, base: str, params: Mapping[str, object] | None = None, *, offline: bool = False,
            refresh: bool = False) -> bytes:
        url = self.canonical_url(base, params)
        key = sha256(url.encode("utf-8")).hexdigest()
        body_path = self.cache_dir / f"{key}.body"
        meta_path = self.cache_dir / f"{key}.json"
        if not refresh or offline:
            cached = self._read_cache(url, body_path, meta_path)
            if cached is not None:
                return cached
        if offline:
            raise OfflineCacheMiss(f"no verified cache entry for {url}")
        with self._lock:
            delay = self.min_interval - (time.monotonic() - self._last_request)
            if delay > 0:
                time.sleep(delay)
            body = self.transport(url, self.headers, self.timeout)
            self._last_request = time.monotonic()
        digest = sha256(body).hexdigest()
        body_path.write_bytes(body)
        meta_path.write_text(json.dumps({"url": url, "fetched_at": time.time(),
                                         "body_sha256": digest}, sort_keys=True), encoding="utf-8")
        return body

    @staticmethod
    def _read_cache(url: str, body_path: Path, meta_path: Path) -> bytes | None:
        if not body_path.is_file() or not meta_path.is_file():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            body = body_path.read_bytes()
            if meta.get("url") != url or meta.get("body_sha256") != sha256(body).hexdigest():
                return None
            return body
        except (OSError, ValueError, TypeError):
            return None

    def json(self, base: str, params: Mapping[str, object] | None = None, **kwargs: object) -> dict:
        try:
            value = json.loads(self.get(base, params, **kwargs).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EvidenceAPIError("API returned invalid JSON") from exc
        if not isinstance(value, dict):
            raise EvidenceAPIError("API returned a non-object JSON document")
        return value
