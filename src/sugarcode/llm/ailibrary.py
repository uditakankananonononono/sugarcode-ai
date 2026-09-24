"""Read-only connector for The AI Library (https://www.theailibrary.co), an AI tools directory.

Discovery only: it reads the public sitemap and public tool pages (robots.txt
allows these) and never posts, submits or signs in. Listing anything on the
site is deliberately not implemented.

* `index()`   - every tool slug from the sitemap (cached for a day)
* `tool(slug)` - title, description and page URL parsed from the tool page
* `search(q)` - slug-word match over the index, then details for the top hits
"""
from __future__ import annotations

import html
import json
import re
import time
import urllib.request
from pathlib import Path

BASE = "https://www.theailibrary.co"
CACHE = Path.home() / ".cache" / "sugarcode" / "ailibrary.json"
_UA = {"User-Agent": "sugarcode-ai (read-only catalog connector)"}
_MIN_GAP = 1.0  # seconds between requests, to stay polite
_last = [0.0]


def _get(url: str, timeout: float = 20.0) -> str:
    wait = _MIN_GAP - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()
    with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_sitemap(xml: str) -> list[str]:
    return sorted({m for m in re.findall(r"<loc>\s*https?://[^/]+/tool/([^<\s/]+)\s*</loc>", xml)})


def parse_tool_page(page: str, slug: str) -> dict:
    def meta(key: str) -> str:
        m = (re.search(rf'<meta[^>]+(?:property|name)="{key}"[^>]+content="([^"]*)"', page)
             or re.search(rf'<meta[^>]+content="([^"]*)"[^>]+(?:property|name)="{key}"', page))
        return html.unescape(m.group(1)).strip() if m else ""
    title = meta("og:title") or html.unescape((re.search(r"<title>(.*?)</title>", page, re.S) or [None, ""])[1]).strip()
    return {"slug": slug, "name": title, "description": meta("og:description") or meta("description"),
            "url": meta("og:url") or f"{BASE}/tool/{slug}"}


def _load_cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {}


def _save_cache(c: dict) -> None:
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(c))
    except OSError:
        pass


def index(max_age_s: int = 86400, refresh: bool = False) -> list[str]:
    c = _load_cache()
    if not refresh and c.get("slugs") and time.time() - c.get("indexed_at", 0) < max_age_s:
        return c["slugs"]
    slugs = parse_sitemap(_get(f"{BASE}/sitemap.xml"))
    c.update(slugs=slugs, indexed_at=time.time())
    _save_cache(c)
    return slugs


def tool(slug: str) -> dict:
    if not re.fullmatch(r"[a-z0-9][a-z0-9\-]*", slug):
        raise ValueError(f"not a tool slug: {slug!r}")
    c = _load_cache()
    hit = c.get("tools", {}).get(slug)
    if hit:
        return hit
    info = parse_tool_page(_get(f"{BASE}/tool/{slug}"), slug)
    c.setdefault("tools", {})[slug] = info
    _save_cache(c)
    return info


def search(query: str, limit: int = 5, details: bool = True) -> list[dict]:
    words = [w for w in re.findall(r"[a-z0-9]+", query.lower()) if len(w) > 1]
    scored = []
    for s in index():
        parts = s.split("-")
        score = sum(2 if w in parts else 1 for w in words if w in s)
        if score:
            scored.append((-score, len(s), s))
    top = [s for _, _, s in sorted(scored)[:limit]]
    return [tool(s) if details else {"slug": s, "url": f"{BASE}/tool/{s}"} for s in top]
