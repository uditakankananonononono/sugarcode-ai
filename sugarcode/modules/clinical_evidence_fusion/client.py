"""Small, module-local NCBI client with stable caching and explicit offline mode."""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_CACHE = Path(os.getenv("SUGARCODE_CLINICAL_CACHE", Path.home() / ".sugarcode_cache" / "clinical_evidence_fusion"))
_LOCK = threading.Lock()
_LAST_REQUEST = 0.0


class NCBIUnavailable(RuntimeError):
    """A live record could not be obtained and no cached record was available."""


class NCBIClient:
    """NCBI E-utilities client respecting the 3 requests/second public limit.

    Responses are content-addressed by SHA-256 of endpoint + sorted parameters.
    A cached response is used until ``ttl_seconds`` expires. In offline mode only
    cached responses are permitted, including expired ones, and their age is
    returned so callers can expose staleness.
    """

    def __init__(self, cache_dir: str | Path | None = None, *, api_key: str | None = None,
                 tool: str = "sugarcode-clinical-evidence-fusion",
                 email: str | None = None, ttl_seconds: int = 86400):
        self.cache_dir = Path(cache_dir) if cache_dir else _CACHE
        self.api_key = api_key or os.getenv("NCBI_API_KEY")
        self.tool, self.email, self.ttl_seconds = tool, email, int(ttl_seconds)

    def _request(self, endpoint: str, params: dict[str, Any], *, offline: bool = False) -> tuple[bytes, dict]:
        full = {**params, "tool": self.tool}
        if self.email:
            full["email"] = self.email
        if self.api_key:
            full["api_key"] = self.api_key
        canonical = endpoint + "?" + urllib.parse.urlencode(sorted(full.items()))
        key = hashlib.sha256(canonical.encode()).hexdigest()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        body_path, meta_path = self.cache_dir / f"{key}.body", self.cache_dir / f"{key}.json"
        now = time.time()
        if body_path.exists():
            age = max(0.0, now - body_path.stat().st_mtime)
            if offline or age <= self.ttl_seconds:
                return body_path.read_bytes(), {"cache": "hit", "age_seconds": round(age, 1),
                                                "offline": offline, "request_sha256": key}
        if offline:
            raise NCBIUnavailable(f"Missing offline cache entry {key} for {endpoint}")
        url = f"{EUTILS}/{endpoint}?{urllib.parse.urlencode(full)}"
        delay, error = 0.6, None
        for attempt in range(4):
            global _LAST_REQUEST
            try:
                with _LOCK:
                    interval = 0.11 if self.api_key else 0.34
                    wait = interval - (time.monotonic() - _LAST_REQUEST)
                    if wait > 0:
                        time.sleep(wait)
                    _LAST_REQUEST = time.monotonic()
                req = urllib.request.Request(url, headers={"User-Agent": f"{self.tool}/1.0"})
                with urllib.request.urlopen(req, timeout=20) as response:
                    body = response.read()
                tmp = body_path.with_suffix(".tmp")
                tmp.write_bytes(body)
                tmp.replace(body_path)
                meta_path.write_text(json.dumps({"url": url, "fetched_at_epoch": time.time()}, indent=2))
                return body, {"cache": "miss", "age_seconds": 0.0, "offline": False,
                              "request_sha256": key}
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                error = exc
                if attempt < 3:
                    time.sleep(delay)
                    delay *= 2
        raise NCBIUnavailable(f"NCBI request failed after 4 attempts: {type(error).__name__}: {error}")

    def clinvar(self, gene: str, hgvs: str, *, retmax: int = 20, offline: bool = False) -> dict:
        needle = hgvs.split(":")[-1].strip()
        term = f'{gene}[gene] AND "{needle}"'
        raw, search_meta = self._request("esearch.fcgi", {"db": "clinvar", "term": term,
                                                          "retmode": "json", "retmax": retmax}, offline=offline)
        ids = json.loads(raw)["esearchresult"]["idlist"]
        if not ids:
            return {"query": term, "records": [], "search_meta": search_meta}
        raw, summary_meta = self._request("esummary.fcgi", {"db": "clinvar", "id": ",".join(ids),
                                                             "retmode": "json"}, offline=offline)
        result = json.loads(raw)["result"]
        records = []
        normalized = needle.lower().replace(" ", "")
        for uid in result.get("uids", []):
            doc = result[uid]
            title = doc.get("title", "")
            germ = doc.get("germline_classification") or {}
            traits = doc.get("trait_set") or []
            records.append({"variation_id": uid, "title": title,
                            "exact_notation_in_title": normalized in title.lower().replace(" ", ""),
                            "classification": germ.get("description") or "Missing",
                            "review_status": germ.get("review_status") or "Missing",
                            "last_evaluated": germ.get("last_evaluated") or "Missing",
                            "conditions": [t.get("trait_name", "Missing") for t in traits],
                            "url": f"https://www.ncbi.nlm.nih.gov/clinvar/variation/{uid}/"})
        return {"query": term, "records": records, "search_meta": search_meta,
                "summary_meta": summary_meta}

    def pubmed(self, query: str, *, retmax: int = 10, offline: bool = False) -> dict:
        raw, search_meta = self._request("esearch.fcgi", {"db": "pubmed", "term": query,
                                                          "retmode": "json", "retmax": retmax,
                                                          "sort": "relevance"}, offline=offline)
        ids = json.loads(raw)["esearchresult"]["idlist"]
        if not ids:
            return {"query": query, "articles": [], "search_meta": search_meta}
        raw, fetch_meta = self._request("efetch.fcgi", {"db": "pubmed", "id": ",".join(ids),
                                                         "retmode": "xml"}, offline=offline)
        root = ET.fromstring(raw)
        articles = []
        for item in root.findall(".//PubmedArticle"):
            pmid = item.findtext(".//PMID") or "Missing"
            title_node = item.find(".//ArticleTitle")
            title = "".join(title_node.itertext()).strip() if title_node is not None else "Missing"
            abst = " ".join("".join(x.itertext()).strip() for x in item.findall(".//AbstractText")) or "Missing"
            year = item.findtext(".//PubDate/Year") or item.findtext(".//ArticleDate/Year") or "Missing"
            articles.append({"pmid": pmid, "title": title, "abstract": abst, "year": year,
                             "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"})
        return {"query": query, "articles": articles, "search_meta": search_meta,
                "fetch_meta": fetch_meta}
