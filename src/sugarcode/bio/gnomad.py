"""Live gnomAD GraphQL connector: population allele frequencies by variant ID."""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://gnomad.broadinstitute.org/api"
CACHE_DIR = Path.home() / ".sugarcode_cache" / "gnomad"
_last_call = 0.0


class GnomADError(RuntimeError):
    pass


def _post(query: str, offline: bool = False, retries: int = 3) -> dict:
    global _last_call
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{abs(hash(query))}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_bytes())
    if offline:
        raise GnomADError("offline mode: no cache for query")
    wait = 0.34 - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()
    body = json.dumps({"query": query}).encode()
    delay = 0.5
    for attempt in range(retries):
        try:
            req = urllib.request.Request(API, data=body,
                                         headers={"Content-Type": "application/json",
                                                  "User-Agent": "sugarcode-ai/0.9"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
            cache_file.write_bytes(json.dumps(data).encode())
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt == retries - 1:
                raise GnomADError(f"gnomAD request failed: {e}") from e
            time.sleep(delay)
            delay *= 2
    raise GnomADError("unreachable")


def variant_frequency(variant_id: str, dataset: str = "gnomad_r4",
                      offline: bool = False) -> dict:
    """Population allele frequency for one variant ('17-7676154-G-C', GRCh38).

    Returns exome/genome AF/AC/AN. A variant absent from gnomAD returns
    present=False - that is a REAL answer (zero observed carriers), stated
    explicitly, distinct from a lookup failure."""
    q = ('{ variant(variantId: "%s", dataset: %s) { variant_id '
         'exome { af an ac } genome { af an ac } } }' % (variant_id, dataset))
    data = _post(q, offline=offline)
    if data.get("errors") and not data.get("data"):
        raise GnomADError(f"gnomAD errors: {data['errors']}")
    v = (data.get("data") or {}).get("variant")
    if v is None:
        return {"variant_id": variant_id, "dataset": dataset, "present": False,
                "note": "no carriers observed in gnomAD - consistent with ultra-rare or absent",
                "exome": None, "genome": None}
    return {"variant_id": v["variant_id"], "dataset": dataset, "present": True,
            "exome": v.get("exome"), "genome": v.get("genome"),
            "max_af": max((v.get("exome") or {}).get("af") or 0.0,
                          (v.get("genome") or {}).get("af") or 0.0)}
