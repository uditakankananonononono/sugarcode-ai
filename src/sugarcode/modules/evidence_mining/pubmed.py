"""PubMed ESearch/EFetch client and conservative XML normalizer."""
from __future__ import annotations
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from .client import CachedHTTPClient, EvidenceAPIError
from .models import EvidenceRecord, MISSING
from .extract import extract_text_evidence

_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class PubMedClient:
    def __init__(self, cache_dir: str | Path, *, email: str | None = None,
                 api_key: str | None = None, http: CachedHTTPClient | None = None):
        self.http = http or CachedHTTPClient(cache_dir, min_interval=0.11 if api_key else 0.34)
        self.email, self.api_key = email, api_key

    def _common(self) -> dict[str, object]:
        return {"tool": "sugarcode-ai", "email": self.email, "api_key": self.api_key}

    def search(self, query: str, *, limit: int = 20, offline: bool = False) -> list[str]:
        if not query.strip():
            raise ValueError("query must not be blank")
        p = {**self._common(), "db": "pubmed", "term": query, "retmode": "json",
             "retmax": max(0, min(int(limit), 10_000)), "sort": "relevance"}
        data = self.http.json(f"{_BASE}/esearch.fcgi", p, offline=offline)
        try:
            return [str(x) for x in data["esearchresult"]["idlist"]]
        except (KeyError, TypeError) as exc:
            raise EvidenceAPIError("malformed PubMed ESearch response") from exc

    def fetch(self, pmids: list[str], *, offline: bool = False) -> list[EvidenceRecord]:
        if not pmids:
            return []
        clean = [p for p in dict.fromkeys(map(str, pmids)) if p.isdigit()]
        if not clean:
            raise ValueError("pmids must contain numeric identifiers")
        p = {**self._common(), "db": "pubmed", "id": ",".join(clean), "retmode": "xml"}
        xml = self.http.get(f"{_BASE}/efetch.fcgi", p, offline=offline)
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as exc:
            raise EvidenceAPIError("malformed PubMed EFetch XML") from exc
        return [_article(a) for a in root.findall(".//PubmedArticle")]

    def query(self, query: str, *, limit: int = 20, offline: bool = False) -> list[EvidenceRecord]:
        return self.fetch(self.search(query, limit=limit, offline=offline), offline=offline)


def _text(node: ET.Element | None) -> str:
    return " ".join("".join(node.itertext()).split()) if node is not None else ""


def _article(a: ET.Element) -> EvidenceRecord:
    pmid = _text(a.find(".//PMID"))
    title = _text(a.find(".//ArticleTitle")) or MISSING
    abstract_parts = [_text(x) for x in a.findall(".//Abstract/AbstractText")]
    abstract = " ".join(x for x in abstract_parts if x)
    doi = MISSING
    for x in a.findall(".//ArticleId"):
        if x.attrib.get("IdType") == "doi" and _text(x):
            doi = _text(x)
    pub_types = [_text(x) for x in a.findall(".//PublicationType") if _text(x)]
    date = next((_text(a.find(path)) for path in (".//ArticleDate", ".//PubDate") if _text(a.find(path))), MISSING)
    mined = extract_text_evidence(abstract)
    return EvidenceRecord(source="PubMed", source_id=pmid or MISSING, title=title,
        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else MISSING,
        publication_date=date, study_type="; ".join(pub_types) or MISSING,
        sample_size=mined["sample_size"], endpoints=mined["endpoints"],
        effect_direction=mined["effect_direction"], effect_text=mined["effect_text"],
        doi=doi, raw={"abstract": abstract, "publication_types": pub_types})
