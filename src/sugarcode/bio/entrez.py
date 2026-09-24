"""Live NCBI E-utilities client: esearch / esummary / efetch.

Real HTTP connector with polite rate limiting (3 req/s, no API key),
exponential-backoff retries, on-disk JSON/XML cache, and an explicit
offline mode for tests and air-gapped runs.
"""
from __future__ import annotations
import http.client
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import hashlib
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
    # stable digest: builtin hash() is salted per process, which made cache
    # files unreachable from any other run and broke --offline reuse
    digest = hashlib.sha256(f"{path}?{key}".encode()).hexdigest()[:32]
    cache_file = CACHE_DIR / f"{digest}.raw"
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
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError,
                http.client.IncompleteRead, ConnectionError) as e:
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
    # [sym] also matches aliases and esearch ranks them first for some
    # symbols: HTT[sym] -> 6532 (SLC6A4, alias HTT), TTN[sym] -> 7276 (TTR).
    # Pick the UID whose official symbol equals the query; validated vs
    # HGNC entrez_id on 60 genes (mega27-01 benchmarks/sweep_entrez_hgnc.json).
    ids = esearch("gene", f"{symbol}[sym] AND {organism}[orgn]", retmax=10, offline=offline)
    if not ids:
        return None
    summ = esummary("gene", ids, offline=offline)
    for u in ids:
        if (summ.get(u, {}).get("name") or "").upper() == symbol.upper():
            return u
    return ids[0]


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


_TX_CORE = __import__("re").compile(
    r"^\s*(?:(?P<tx>[A-Z]{2}_\d+(?:\.\d+)?)(?:\([^)]*\))?:)?(?P<core>[cgmnp]\.[^\s()]+(?:\([^)]*\))?[^\s()]*)")


def _hgvs_core(notation: str) -> str | None:
    """'NM_000038.6(APC):c.1668T>C (p.Asp556=)' -> 'c.1668T>C'."""
    m = _TX_CORE.match((notation or "").strip().strip('"'))
    return m.group("core") if m else None


def clinvar_query(gene: str, notation: str) -> str:
    """ClinVar esearch term for one variant. ClinVar names carry a trailing
    ' (p.X)' that breaks a quoted phrase query, so the query uses the
    transcript-qualified c. core when a transcript is given (1 exact hit in
    the 8-variant pilot) and gene + core otherwise."""
    n = (notation or "").strip().strip('"')
    m = _TX_CORE.match(n)
    if not m:
        return f'{gene}[gene] AND "{n.split(":")[-1]}"'
    core, tx = m.group("core"), m.group("tx")
    if tx:
        return f'"{tx}:{core}"'
    return f'{gene}[gene] AND "{core}"'


def clinvar_exact(gene: str, notation: str, offline: bool = False) -> list[dict]:
    """Targeted ClinVar lookup for one variant notation (e.g. 'c.68_69del',
    'p.Arg273His'). Uses a quoted phrase query - far better than paging the
    gene's whole variant set."""
    ids = esearch("clinvar", clinvar_query(gene, notation), retmax=20, offline=offline)
    core = _hgvs_core(notation)
    fallback = f'{gene}[gene] AND "{core}"' if core else None
    if not ids and fallback and fallback != clinvar_query(gene, notation):
        # transcript-qualified phrase missed (e.g. version drift): gene + core
        try:
            ids = esearch("clinvar", fallback, retmax=20, offline=offline)
        except EntrezError:
            if not offline:
                raise
            ids = []
    out = []
    for uid, doc in esummary("clinvar", ids, offline=offline).items():
        germ = doc.get("germline_classification", {})
        out.append({"uid": uid, "title": doc.get("title", ""),
                    "significance": germ.get("description", "uncertain"),
                    "review_status": germ.get("review_status", ""),
                    "condition": (doc.get("trait_set") or [{}])[0].get("trait_name", "")})
    return out

