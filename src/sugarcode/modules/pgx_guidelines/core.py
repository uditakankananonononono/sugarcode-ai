"""Deterministic CPIC-aligned pharmacogenomic decision support.

Only explicitly supplied diplotypes are interpreted. This module never infers a
star allele from raw variants and never substitutes for a prescribing clinician.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .client import LiteratureUnavailable, PubMedClient

GUIDELINES = {
    "CYP2C19:CLOPIDOGREL": {
        "title": "CPIC Guideline for CYP2C19 Genotype and Clopidogrel Therapy: 2022 Update",
        "pmid": "35034351", "doi": "10.1002/cpt.2526", "published": "2022",
        "scope": "cardiovascular indications; recommendation depends on clinical context",
    },
    "CYP2D6:CODEINE": {
        "title": "CPIC guideline for CYP2D6, OPRM1, and COMT genotypes and select opioid therapy",
        "pmid": "33387367", "doi": "10.1002/cpt.2149", "published": "2021",
        "scope": "codeine therapy; age, pregnancy/lactation, organ function, interactions, and local labeling still apply",
    },
}

# CYP2C19 function values per CPIC phenotype translation conventions.
_C19 = {"*1": 1.0, "*2": 0.0, "*3": 0.0, "*4": 0.0, "*5": 0.0, "*6": 0.0,
        "*7": 0.0, "*8": 0.0, "*17": 1.5}
# CYP2D6 activity values used by CPIC/DPWG consensus. Copy-number syntax: *1x2.
_D6 = {"*1": 1.0, "*2": 1.0, "*3": 0.0, "*4": 0.0, "*5": 0.0, "*6": 0.0,
       "*9": 0.5, "*10": 0.25, "*17": 0.5, "*29": 0.5, "*41": 0.5}


def _split(diplotype: str) -> list[str]:
    parts = [x.strip() for x in diplotype.replace("|", "/").split("/")]
    if len(parts) != 2 or any(not x.startswith("*") for x in parts):
        raise ValueError("diplotype must contain two star alleles, for example *1/*2")
    return parts


def _allele_value(allele: str, table: dict[str, float]) -> tuple[float | None, str | None]:
    lower = allele.lower()
    copies = 1
    if "x" in lower:
        base, count = lower.rsplit("x", 1)
        if not count.isdigit() or int(count) < 1: return None, "invalid copy-number suffix"
        allele, copies = base, int(count)
    value = table.get(allele)
    return ((value * copies, None) if value is not None else (None, "allele function Missing"))


def translate_phenotype(gene: str, diplotype: str) -> dict:
    """Translate a known star diplotype via published CPIC activity conventions."""
    gene = gene.upper(); alleles = _split(diplotype)
    table = _C19 if gene == "CYP2C19" else _D6 if gene == "CYP2D6" else None
    if table is None:
        return {"gene": gene, "diplotype": diplotype, "phenotype": "Missing", "activity_score": "Missing",
                "status": "unsupported gene; no phenotype inferred"}
    values, problems = [], []
    for allele in alleles:
        value, problem = _allele_value(allele, table)
        if problem: problems.append(f"{allele}: {problem}")
        else: values.append(value)
    if problems:
        return {"gene": gene, "diplotype": diplotype, "phenotype": "Missing", "activity_score": "Missing",
                "status": "; ".join(problems), "known_alleles": sorted(table)}
    score = round(sum(values), 2)
    if gene == "CYP2D6":
        phenotype = ("Poor metabolizer" if score == 0 else "Intermediate metabolizer" if score < 1.25
                     else "Normal metabolizer" if score <= 2.25 else "Ultrarapid metabolizer")
    else:
        # CPIC CYP2C19 translation: increased-function + normal = rapid; two increased = ultrarapid.
        phenotype = ("Poor metabolizer" if score == 0 else "Intermediate metabolizer" if score <= 1.5
                     else "Normal metabolizer" if score == 2 else "Rapid metabolizer" if score == 2.5
                     else "Ultrarapid metabolizer" if score >= 3 else "Indeterminate")
    return {"gene": gene, "diplotype": "/".join(alleles), "phenotype": phenotype,
            "activity_score": score, "status": "translated", "allele_values": dict(zip(alleles, values)),
            "provenance": "CPIC/PharmGKB allele-function and phenotype translation tables; caller must verify phased star-allele call"}


def _recommend(gene: str, drug: str, phenotype: str, indication: str | None) -> dict:
    key = f"{gene}:{drug}"
    if key == "CYP2C19:CLOPIDOGREL":
        if phenotype in {"Intermediate metabolizer", "Poor metabolizer"}:
            action = "Consider an alternative P2Y12 inhibitor not affected by CYP2C19 loss of function."
            strength = "Strong for acute coronary syndrome/PCI; moderate for other cardiovascular indications"
        elif phenotype in {"Normal metabolizer", "Rapid metabolizer", "Ultrarapid metabolizer"}:
            action, strength = "Use clopidogrel at the guideline-directed standard dose.", "Strong"
        else: action, strength = "No recommendation: phenotype is indeterminate or Missing.", "Missing"
        return {"recommendation": action, "strength": strength,
                "alternatives_note": "Prasugrel or ticagrelor may be alternatives when clinically appropriate; contraindications and indication must be checked.",
                "indication": indication or "Missing - recommendation strength is context dependent"}
    if key == "CYP2D6:CODEINE":
        if phenotype in {"Poor metabolizer", "Ultrarapid metabolizer"}:
            action, strength = "Avoid codeine because of diminished efficacy (poor) or toxicity risk (ultrarapid).", "Strong"
        elif phenotype == "Intermediate metabolizer":
            action, strength = "Use age- or weight-specific label dosing; if no response, consider a non-tramadol alternative not affected by CYP2D6.", "Moderate"
        elif phenotype == "Normal metabolizer":
            action, strength = "Use age- or weight-specific label dosing.", "Strong"
        else: action, strength = "No recommendation: phenotype is indeterminate or Missing.", "Missing"
        return {"recommendation": action, "strength": strength,
                "alternatives_note": "Choice of analgesic requires patient-specific assessment and local regulatory restrictions.",
                "indication": indication or "pain"}
    return {"recommendation": "Missing", "strength": "Missing",
            "reason": "No module guideline for this gene-drug pair"}


def assess(gene: str, diplotype: str, drug: str, *, indication: str | None = None,
           interacting_drugs: Iterable[str] = (), offline: bool = False,
           verify_publication: bool = True, client: PubMedClient | None = None) -> dict:
    """Return auditable phenotype translation and CPIC-aligned drug guidance."""
    gene, drug = gene.upper(), drug.upper()
    translation = translate_phenotype(gene, diplotype)
    key = f"{gene}:{drug}"
    guideline = GUIDELINES.get(key)
    output = {"input": {"gene": gene, "diplotype": diplotype, "drug": drug,
                         "indication": indication or "Missing", "interacting_drugs": list(interacting_drugs)},
              "phenotype_translation": translation,
              "guidance": _recommend(gene, drug, translation["phenotype"], indication),
              "guideline": guideline or {"status": "Missing"},
              "safety": {"prescribing_status": "decision support only; clinician and pharmacist review required",
                         "phenoconversion_warning": "CYP inhibitors/inducers, organ function, age, ancestry-dependent allele coverage, and assay limitations can make genotype-predicted phenotype differ from observed metabolism.",
                         "raw_variant_warning": "Do not derive a star allele from raw variants with this module.",
                         "missing_is_not_negative": True}}
    if verify_publication and guideline:
        try:
            output["publication_live"] = (client or PubMedClient()).guideline(guideline["pmid"], offline=offline)
        except LiteratureUnavailable as exc:
            output["publication_live"] = {"status": "Missing", "error": str(exc),
                                          "note": "Guidance provenance remains declared, but live PubMed verification failed."}
    return output
