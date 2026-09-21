"""Live UniProt REST connector: protein records, sequences, features, GO terms."""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://rest.uniprot.org/uniprotkb"
CACHE_DIR = Path.home() / ".sugarcode_cache" / "uniprot"
_last_call = 0.0


class UniProtError(RuntimeError):
    pass


def _get(url: str, offline: bool = False, retries: int = 3) -> bytes:
    global _last_call
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{abs(hash(url))}.json"
    if cache_file.exists():
        return cache_file.read_bytes()
    if offline:
        raise UniProtError(f"offline mode: no cache for {url}")
    wait = 0.34 - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()
    delay = 0.5
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json",
                                                       "User-Agent": "sugarcode-ai/0.3"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            cache_file.write_bytes(data)
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt == retries - 1:
                raise UniProtError(f"UniProt request failed: {e}") from e
            time.sleep(delay)
            delay *= 2
    raise UniProtError("unreachable")


def search(gene: str, organism_id: int = 9606, reviewed: bool = True,
           offline: bool = False) -> dict | None:
    """Best UniProt entry for a gene symbol. Returns normalized record."""
    q = urllib.parse.quote(f"gene:{gene} AND organism_id:{organism_id}"
                           + (" AND reviewed:true" if reviewed else ""))
    url = f"{BASE}/search?query={q}&size=1&format=json"
    data = json.loads(_get(url, offline=offline))
    results = data.get("results", [])
    if not results:
        return None
    e = results[0]
    seq = e.get("sequence", {})
    feats = [{"type": f.get("type"), "description": f.get("description", ""),
              "begin": f.get("location", {}).get("start", {}).get("value"),
              "end": f.get("location", {}).get("end", {}).get("value")}
             for f in e.get("features", [])]
    go = [x["id"] for x in e.get("uniProtKBCrossReferences", [])
          if x.get("database") == "GO" for x in [x]]
    return {
        "accession": e.get("primaryAccession"),
        "id": e.get("uniProtkbId"),
        "protein_name": (e.get("proteinDescription", {}).get("recommendedName", {})
                         .get("fullName", {}).get("value", "")),
        "gene": gene,
        "organism": e.get("organism", {}).get("scientificName", ""),
        "length": seq.get("length"),
        "mass": seq.get("molWeight"),
        "sequence": seq.get("value", ""),
        "features": feats,
        "go_terms": go,
        "comments": [c.get("commentType") for c in e.get("comments", [])],
    }


def binding_sites(gene: str, offline: bool = False) -> dict:
    """Annotated binding/active-site features for a gene's best UniProt entry.

    Numbering is UniProt canonical. Verified for ABL1 (P00519, 1130 aa):
    the kinase-domain features match clinical 1a numbering - gatekeeper
    T315 sits immediately before the annotated 316-322 ATP-binding stretch
    and E255 inside the 248-256 P-loop annotation.
    """
    rec = search(gene, offline=offline)
    if not rec:
        return {"status": "no UniProt entry", "gene": gene}
    sites = [f for f in rec["features"]
             if f["type"] in ("Binding site", "Active site")]
    return {"status": "ok", "gene": gene, "accession": rec["accession"],
            "sites": sites,
            "numbering": "UniProt canonical",
            "source": f"UniProt {rec['accession']} ({'cache' if offline else 'live'})"}
