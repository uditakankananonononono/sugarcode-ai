"""Module-local PubMed client for retrieving current pharmacogenomic guidance."""
from __future__ import annotations
import hashlib, json, os, threading, time
import urllib.error, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_LOCK = threading.Lock()
_LAST = 0.0


class LiteratureUnavailable(RuntimeError):
    pass


class PubMedClient:
    """Cached, throttled NCBI client. Offline mode never touches the network."""
    def __init__(self, cache_dir: str | Path | None = None, ttl_seconds: int = 86400):
        self.cache_dir = Path(cache_dir or os.getenv("SUGARCODE_PGX_CACHE",
                              Path.home() / ".sugarcode_cache" / "pgx_guidelines"))
        self.ttl_seconds = int(ttl_seconds)

    def _get(self, endpoint: str, params: dict, offline: bool) -> tuple[bytes, dict]:
        params = {**params, "tool": "sugarcode-pgx-guidelines"}
        key = hashlib.sha256((endpoint + "?" + urllib.parse.urlencode(sorted(params.items()))).encode()).hexdigest()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        path = self.cache_dir / f"{key}.body"
        if path.exists():
            age = max(0, time.time() - path.stat().st_mtime)
            if offline or age <= self.ttl_seconds:
                return path.read_bytes(), {"cache": "hit", "age_seconds": round(age, 1),
                                           "offline": offline, "request_sha256": key}
        if offline:
            raise LiteratureUnavailable(f"Missing offline cache entry {key}")
        api_key = os.getenv("NCBI_API_KEY")
        if api_key:
            params["api_key"] = api_key
        url = f"{BASE}/{endpoint}?{urllib.parse.urlencode(params)}"
        error = None
        for attempt in range(4):
            global _LAST
            try:
                with _LOCK:
                    interval = 0.11 if api_key else 0.34
                    wait = interval - (time.monotonic() - _LAST)
                    if wait > 0: time.sleep(wait)
                    _LAST = time.monotonic()
                with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "sugarcode-pgx/1.0"}), timeout=20) as r:
                    body = r.read()
                tmp = path.with_suffix(".tmp"); tmp.write_bytes(body); tmp.replace(path)
                return body, {"cache": "miss", "age_seconds": 0, "offline": False,
                              "request_sha256": key}
            except (OSError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError) as exc:
                error = exc
                if attempt < 3: time.sleep(0.5 * (2 ** attempt))
        raise LiteratureUnavailable(f"PubMed unavailable after retries: {type(error).__name__}: {error}")

    def guideline(self, pmid: str, offline: bool = False) -> dict:
        body, meta = self._get("efetch.fcgi", {"db": "pubmed", "id": pmid, "retmode": "xml"}, offline)
        root = ET.fromstring(body)
        article = root.find(".//PubmedArticle")
        if article is None:
            return {"pmid": pmid, "status": "Missing", "retrieval": meta}
        title_node = article.find(".//ArticleTitle")
        title = "".join(title_node.itertext()).strip() if title_node is not None else "Missing"
        abstract = " ".join("".join(n.itertext()).strip() for n in article.findall(".//AbstractText")) or "Missing"
        year = article.findtext(".//PubDate/Year") or article.findtext(".//ArticleDate/Year") or "Missing"
        doi = "Missing"
        for node in article.findall(".//ArticleId"):
            if node.attrib.get("IdType") == "doi": doi = node.text or "Missing"
        return {"pmid": pmid, "title": title, "abstract": abstract, "year": year, "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", "retrieval": meta}
