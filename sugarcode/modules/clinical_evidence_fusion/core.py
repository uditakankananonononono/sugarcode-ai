"""Clinically cautious fusion of live ClinVar records and ACMG/AMP evidence.

The classifier implements the Bayesian calibration described by Tavtigian et al.
It estimates *variant pathogenicity*, not disease penetrance or patient risk.
"""
from __future__ import annotations

from collections import Counter
from math import prod
from typing import Iterable

from .client import NCBIClient, NCBIUnavailable

MODEL_PROVENANCE = {
    "framework": "ACMG/AMP sequence variant interpretation with Bayesian calibration",
    "publication": "Tavtigian et al., Genetics in Medicine 2018;20:1054-1060",
    "doi": "10.1038/gim.2017.210",
    "pmid": "29300386",
    "prior_probability": 0.10,
    "important_limit": "Posterior is a model-calibrated probability of pathogenicity, not penetrance or patient disease risk.",
}

# Likelihood ratios calibrated in Tavtigian et al. Benign strengths use reciprocal odds.
_LR = {"very_strong": 350.0, "strong": 18.7, "moderate": 4.3, "supporting": 2.08,
       "stand_alone": 1000.0}
_ALLOWED_CODES = {
    "PVS1": ("pathogenic", "very_strong"),
    **{f"PS{i}": ("pathogenic", "strong") for i in range(1, 5)},
    **{f"PM{i}": ("pathogenic", "moderate") for i in range(1, 7)},
    **{f"PP{i}": ("pathogenic", "supporting") for i in range(1, 6)},
    "BA1": ("benign", "stand_alone"),
    **{f"BS{i}": ("benign", "strong") for i in range(1, 5)},
    **{f"BP{i}": ("benign", "supporting") for i in range(1, 8)},
}
_REVIEW_WEIGHT = {"practice guideline": 4, "reviewed by expert panel": 3,
                  "criteria provided, multiple submitters, no conflicts": 2,
                  "criteria provided, conflicting classifications": 0,
                  "criteria provided, single submitter": 1,
                  "no assertion criteria provided": 0,
                  "no assertion provided": 0}


def bayesian_acmg(criteria: Iterable[str | dict], *, prior_probability: float = 0.10) -> dict:
    """Apply published Bayesian odds to explicitly supplied ACMG evidence.

    Each item is an ACMG code (default published strength) or a mapping with
    ``code`` and optional ``strength``. Unknown codes and invalid strengths are
    retained under ``rejected_evidence`` rather than silently ignored.
    """
    if not 0 < prior_probability < 1:
        raise ValueError("prior_probability must be between 0 and 1")
    accepted, rejected = [], []
    for raw in criteria:
        item = {"code": raw} if isinstance(raw, str) else dict(raw)
        code = str(item.get("code", "")).upper()
        if code not in _ALLOWED_CODES:
            rejected.append({"input": raw, "reason": "unknown ACMG/AMP evidence code"})
            continue
        direction, default_strength = _ALLOWED_CODES[code]
        strength = str(item.get("strength", default_strength)).lower()
        if strength not in _LR:
            rejected.append({"input": raw, "reason": "unknown evidence strength"})
            continue
        lr = _LR[strength] if direction == "pathogenic" else 1 / _LR[strength]
        accepted.append({"code": code, "direction": direction, "strength": strength,
                         "likelihood_ratio": round(lr, 8),
                         "provenance": item.get("provenance", "user-supplied; not independently validated")})
    prior_odds = prior_probability / (1 - prior_probability)
    posterior_odds = prior_odds * prod(x["likelihood_ratio"] for x in accepted)
    posterior = posterior_odds / (1 + posterior_odds)
    pathogenic = any(x["direction"] == "pathogenic" for x in accepted)
    benign = any(x["direction"] == "benign" for x in accepted)
    conflict = pathogenic and benign
    # ClinGen Bayesian boundaries mapped to ACMG five-tier labels. With no
    # accepted evidence we deliberately retain VUS rather than interpreting
    # the framework prior as affirmative likely-benign evidence.
    if not accepted:
        label = "Uncertain significance"
    elif posterior >= 0.99:
        label = "Pathogenic"
    elif posterior >= 0.90:
        label = "Likely pathogenic"
    elif posterior <= 0.001:
        label = "Benign"
    elif posterior <= 0.10:
        label = "Likely benign"
    else:
        label = "Uncertain significance"
    return {"classification": label, "posterior_probability_pathogenic": round(posterior, 6),
            "prior_probability": prior_probability, "accepted_evidence": accepted,
            "rejected_evidence": rejected, "directional_conflict": conflict,
            "uncertainty": _uncertainty(label, conflict, len(accepted), len(rejected)),
            "model_provenance": {**MODEL_PROVENANCE, "prior_probability": prior_probability}}


def _uncertainty(label: str, conflict: bool, accepted: int, rejected: int) -> dict:
    reasons = []
    if not accepted:
        reasons.append("No valid ACMG/AMP evidence criteria were supplied; posterior equals prior.")
    if conflict:
        reasons.append("Pathogenic and benign evidence coexist; independent expert adjudication is required.")
    if rejected:
        reasons.append(f"{rejected} evidence item(s) were rejected and did not affect the score.")
    if label == "Uncertain significance":
        reasons.append("VUS is not actionable and must not be treated as pathogenic or benign.")
    return {"is_vus": label == "Uncertain significance", "reasons": reasons or ["No model-specific warning."],
            "missing_labels_are_literal": True}


def _review_weight(status: str) -> int:
    lowered = status.lower()
    return max((weight for phrase, weight in _REVIEW_WEIGHT.items() if phrase in lowered), default=0)


def summarize_clinvar(records: list[dict]) -> dict:
    """Summarize exact ClinVar records without overriding conflicts or VUS."""
    exact = [r for r in records if r.get("exact_notation_in_title")]
    pool = exact or records
    counts = Counter((r.get("classification") or "Missing") for r in pool)
    ranked = sorted(pool, key=lambda r: _review_weight(r.get("review_status", "")), reverse=True)
    top_weight = _review_weight(ranked[0].get("review_status", "")) if ranked else -1
    top = [r for r in ranked if _review_weight(r.get("review_status", "")) == top_weight]
    top_labels = {r.get("classification", "Missing") for r in top}
    if not pool:
        consensus = "Missing"
        warning = "No matching ClinVar record was returned. Absence is not evidence of benignity."
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
                     include_literature: bool = True, client: NCBIClient | None = None) -> dict:
    """Fuse live ClinVar/PubMed evidence with a transparent Bayesian score.

    Live records are reported beside, not injected into, the ACMG score because
    turning an aggregate ClinVar label into an ACMG code would double-count
    submitter evidence. ``Missing`` is emitted literally for unavailable fields.
    """
    client = client or NCBIClient()
    result = {"query": {"gene": gene.upper(), "hgvs": hgvs, "phenotype": phenotype or "Missing"},
              "bayesian_acmg": bayesian_acmg(criteria),
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
