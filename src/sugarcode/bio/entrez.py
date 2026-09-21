"""Live NCBI E-utilities client: esearch / esummary / efetch.

Real HTTP connector with polite rate limiting (3 req/s, no API key),
exponential-backoff retries, on-disk JSON/XML cache, and an explicit
offline mode for tests and air-gapped runs.
"""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
_MIN_INTERVAL = 0.34  # seconds between requests (NCBI: 3/s without API key)
_last_call = 0.0
CACHE_DIR = Path.home() / ".sugarcode_cache" / "entrez"


class EntrezError(RuntimeError):
    pass


def _throttle():
    global _last_call
    wait = _MIN_INTERVAL - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()


def _get(path: str, params: dict, offline: bool = False, retries: int = 3) -> bytes:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = urllib.parse.urlencode(sorted(params.items()))
    cache_file = CACHE_DIR / f"{abs(hash((path, key)))}.raw"
    if cache_file.exists():
        return cache_file.read_bytes()
    if offline:
        raise EntrezError(f"offline mode: no cache for {path}?{key}")
    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
    delay = 0.5
    for attempt in range(retries):
        _throttle()
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                data = r.read()
            cache_file.write_bytes(data)
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt == retries - 1:
                raise EntrezError(f"E-utilities request failed after {retries} tries: {e}") from e
            time.sleep(delay)
            delay *= 2
    raise EntrezError("unreachable")


def esearch(db: str, term: str, retmax: int = 20, offline: bool = False) -> list[str]:
    """Search a database, return ID list."""
    data = _get("esearch.fcgi", {"db": db, "term": term, "retmode": "json",
                                 "retmax": retmax}, offline=offline)
    return json.loads(data)["esearchresult"]["idlist"]


def esummary(db: str, ids: list[str], offline: bool = False) -> dict[str, dict]:
    """Summaries for IDs, keyed by UID."""
    if not ids:
        return {}
    data = _get("esummary.fcgi", {"db": db, "id": ",".join(ids), "retmode": "json"},
                offline=offline)
    res = json.loads(data)["result"]
    return {u: res[u] for u in res["uids"] if u in res}


def efetch_fasta(db: str, uid: str, offline: bool = False) -> str:
    """Raw FASTA text for a nucleotide/protein record."""
    return _get("efetch.fcgi", {"db": db, "id": uid, "rettype": "fasta",
                                "retmode": "text"}, offline=offline).decode()


def efetch_xml(db: str, ids: list[str], offline: bool = False) -> ET.Element:
    """Parsed XML tree for a batch of records."""
    if not ids:
        return ET.Element("empty")
    data = _get("efetch.fcgi", {"db": db, "id": ",".join(ids), "retmode": "xml"},
                offline=offline)
    return ET.fromstring(data)


def gene_id(symbol: str, organism: str = "human", offline: bool = False) -> str | None:
    """Resolve a gene symbol to its NCBI Gene UID."""
    ids = esearch("gene", f"{symbol}[sym] AND {organism}[orgn]", retmax=1, offline=offline)
    return ids[0] if ids else None


def pubmed_ids(query: str, retmax: int = 10, offline: bool = False) -> list[str]:
    return esearch("pubmed", query, retmax=retmax, offline=offline)


def pubmed_abstracts(pmids: list[str], offline: bool = False) -> list[dict]:
    """Fetch abstracts as structured records: pmid, title, abstract, year, journal."""
    root = efetch_xml("pubmed", pmids, offline=offline)
    out = []
    for art in root.iter("PubmedArticle"):
        pmid = art.findtext(".//PMID") or ""
        title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
        abstract = " ".join("".join(a.itertext()) for a in art.findall(".//AbstractText"))
        year = art.findtext(".//PubDate/Year") or art.findtext(".//PubDate/MedlineDate") or ""
        journal = art.findtext(".//Journal/Title") or ""
        out.append({"pmid": pmid, "title": title.strip(), "abstract": abstract.strip(),
                    "year": year[:4], "journal": journal})
    return out


def clinvar_variants(gene: str, retmax: int = 20, offline: bool = False) -> list[dict]:
    """Live ClinVar summaries for a gene: variation, significance, review status."""
    ids = esearch("clinvar", f"{gene}[gene]", retmax=retmax, offline=offline)
    out = []
    for uid, doc in esummary("clinvar", ids, offline=offline).items():
        germ = doc.get("germline_classification", {})
        out.append({
            "uid": uid,
            "title": doc.get("title", ""),
            "significance": germ.get("description", "uncertain"),
            "review_status": germ.get("review_status", ""),
            "condition": (doc.get("trait_set") or [{}])[0].get("trait_name", ""),
        })
    return out


def clinvar_exact(gene: str, notation: str, offline: bool = False) -> list[dict]:
    """Targeted ClinVar lookup for one variant notation (e.g. 'c.68_69del',
    'p.Arg273His'). Uses a quoted phrase query - far better than paging the
    gene's whole variant set."""
    needle = notation.split(":")[-1].strip('"')
    ids = esearch("clinvar", f"{gene}[gene] AND \"{needle}\"", retmax=20, offline=offline)
    out = []
    for uid, doc in esummary("clinvar", ids, offline=offline).items():
        germ = doc.get("germline_classification", {})
        out.append({"uid": uid, "title": doc.get("title", ""),
                    "significance": germ.get("description", "uncertain"),
                    "review_status": germ.get("review_status", ""),
                    "condition": (doc.get("trait_set") or [{}])[0].get("trait_name", "")})
    return out
