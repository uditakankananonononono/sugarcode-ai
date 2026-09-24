"""Optional live lookup layer: NCBI ClinVar records and PubMed search results
reported beside (never injected into) the Bayesian ACMG score.

Turning an aggregate ClinVar label into an ACMG code would double-count the
submitters' underlying evidence, so ClinVar and PubMed are context only.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable

from .client import NCBIClient, NCBIUnavailable
from .core import PRIOR_PROBABILITY, bayesian_acmg

_REVIEW_WEIGHT = {"practice guideline": 4, "reviewed by expert panel": 3,
                  "criteria provided, multiple submitters, no conflicts": 2,
                  "criteria provided, conflicting classifications": 0,
                  "criteria provided, single submitter": 1,
                  "no assertion criteria provided": 0,
                  "no assertion provided": 0}



def _review_weight(status: str) -> int:
    lowered = status.lower()
    return max((weight for phrase, weight in _REVIEW_WEIGHT.items() if phrase in lowered), default=0)


def summarize_clinvar(records: list[dict]) -> dict:
    """Summarize exact ClinVar records without overriding conflicts or VUS."""
    exact = [r for r in records if r.get("exact_notation_in_title")]
    # Only records whose title carries the queried variant are summarised.
    # ClinVar full-text search also returns unrelated variants in the gene;
    # those are kept in ``records`` for transparency but never counted.
    pool = exact
    counts = Counter((r.get("classification") or "Missing") for r in pool)
    ranked = sorted(pool, key=lambda r: _review_weight(r.get("review_status", "")), reverse=True)
    top_weight = _review_weight(ranked[0].get("review_status", "")) if ranked else -1
    top = [r for r in ranked if _review_weight(r.get("review_status", "")) == top_weight]
    top_labels = {r.get("classification", "Missing") for r in top}
    if not pool:
        consensus = "Missing"
        warning = ("No ClinVar record matching this exact variant was returned"
                   + (f" ({len(records)} non-matching record(s) ignored)" if records else "")
                   + ". Absence is not evidence of benignity.")
    elif len(top_labels) > 1 or any("conflict" in x.lower() for x in counts):
        consensus = "Conflicting"
        warning = "ClinVar classifications conflict. Do not collapse this to a pathogenic or benign call."
    else:
        consensus = next(iter(top_labels))
        warning = ("ClinVar aggregate classification is evidence, not a diagnosis. Verify phenotype, inheritance, and record recency.")
    return {"consensus": consensus, "classification_counts": dict(counts),
            "exact_record_count": len(exact), "returned_record_count": len(records),
            "highest_review_weight": max(top_weight, 0), "warning": warning,
            "records": records}


def evaluate_variant(gene: str, hgvs: str, *, criteria: Iterable[str | dict] = (),
                     phenotype: str | None = None, offline: bool = False,
                     include_literature: bool = True, client: NCBIClient | None = None,
                     prior_probability: float = PRIOR_PROBABILITY) -> dict:
    """Fuse live ClinVar/PubMed evidence with a transparent Bayesian score.

    Live records are reported beside, not injected into, the ACMG score because
    turning an aggregate ClinVar label into an ACMG code would double-count
    submitter evidence. ``Missing`` is emitted literally for unavailable fields.
    """
    client = client or NCBIClient()
    result = {"query": {"gene": gene.upper(), "hgvs": hgvs, "phenotype": phenotype or "Missing"},
              "bayesian_acmg": bayesian_acmg(criteria, prior_probability=prior_probability),
              "clinical_use": "research and clinician decision support only; not a diagnosis or treatment recommendation"}
    try:
        cv = client.clinvar(gene.upper(), hgvs, offline=offline)
        result["clinvar"] = {**summarize_clinvar(cv["records"]),
                             "query": cv["query"], "retrieval": {k: v for k, v in cv.items() if k.endswith("_meta")},
                             "source": "NCBI ClinVar", "source_url": "https://www.ncbi.nlm.nih.gov/clinvar/"}
    except NCBIUnavailable as exc:
        result["clinvar"] = {"consensus": "Missing", "records": [], "error": str(exc),
                             "warning": "ClinVar unavailable; no classification was inferred."}
    if include_literature:
        pub_query = f'({gene}[Title/Abstract]) AND ("{hgvs.split(":")[-1]}"[Title/Abstract])'
        if phenotype:
            pub_query += f' AND ({phenotype}[Title/Abstract])'
        try:
            lit = client.pubmed(pub_query, offline=offline)
            result["literature"] = {**lit, "source": "NCBI PubMed",
                                    "screening_status": "unscreened search results; relevance is not evidence quality"}
        except NCBIUnavailable as exc:
            result["literature"] = {"articles": [], "status": "Missing", "error": str(exc)}
    return result
