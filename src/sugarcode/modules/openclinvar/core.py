from __future__ import annotations
from ...bio.sequence import STANDARD_CODE, AA_NAMES

# ACMG-style evidence rules (simplified but mechanistic)
CONSEQUENCE_WEIGHTS = {
    "nonsense": 0.9, "frameshift": 0.95, "splice_disruption": 0.9,
    "missense": 0.45, "inframe_indel": 0.4, "synonymous": 0.05,
    "utr": 0.15, "intronic": 0.1, "intergenic": 0.05,
}
# small built-in reference of well-known pathogenic/likely-benign exemplars
KNOWN = {
    ("BRCA1", "c.68_69delAG"): ("pathogenic", "founder frameshift, loss of function"),
    ("CFTR", "p.Phe508del"): ("pathogenic", "inframe deletion, folding defect, cystic fibrosis"),
    ("HBB", "c.20A>T"): ("pathogenic", "sickle-cell Glu6Val missense"),
    ("APOE", "p.Cys130Arg"): ("risk_factor", "APOE4 allele, Alzheimer risk modifier"),
    ("TP53", "p.Arg248Trp"): ("pathogenic", "DNA-contact hotspot missense"),
}


def parse_vcf_line(line: str) -> dict:
    f = line.rstrip("\n").split("\t")
    if len(f) < 5 or line.startswith("#"):
        raise ValueError("not a VCF data line")
    return {"chrom": f[0], "pos": int(f[1]), "id": f[2], "ref": f[3], "alt": f[4],
            "info": f[7] if len(f) > 7 else ""}


def _classify_consequence(ref_codon: str, alt_codon: str) -> str:
    ra, aa = STANDARD_CODE.get(ref_codon, "X"), STANDARD_CODE.get(alt_codon, "X")
    if ra == aa:
        return "synonymous"
    if aa == "*":
        return "nonsense"
    return "missense"


def interpret_variant(gene: str, variant: str, consequence: str | None = None,
                      ref_codon: str | None = None, alt_codon: str | None = None,
                      allele_frequency: float | None = None,
                      functional_score: float | None = None,
                      segregation: bool | None = None) -> dict:
    """Evidence-weighted variant interpretation with explanation trace.

    Inputs mirror VCF/ClinVar fields; outputs ACMG-flavored classification,
    per-evidence contributions and plain-language explanation.
    """
    evidence: list[dict] = []
    if consequence is None and ref_codon and alt_codon:
        consequence = _classify_consequence(ref_codon, alt_codon)
    consequence = consequence or "missense"
    base = CONSEQUENCE_WEIGHTS.get(consequence, 0.3)
    evidence.append({"rule": "consequence_type", "weight": base,
                     "detail": f"{consequence} baseline weight {base}"})

    if (gene, variant) in KNOWN:
        cls, why = KNOWN[(gene, variant)]
        evidence.append({"rule": "curated_record", "weight": 1.0,
                         "detail": f"known {cls}: {why}"})
        return _result(gene, variant, consequence, cls, 0.98, evidence,
                       curated_note=why)

    score = base
    if allele_frequency is not None:
        if allele_frequency > 0.05:
            score -= 0.5
            evidence.append({"rule": "BA1_common", "weight": -0.5,
                             "detail": f"allele frequency {allele_frequency:.3f} too common for pathogenic"})
        elif allele_frequency < 0.0001:
            score += 0.15
            evidence.append({"rule": "PM2_rare", "weight": 0.15,
                             "detail": "extremely rare in population databases"})
    if functional_score is not None:
        w = 0.25 * functional_score
        score += w
        evidence.append({"rule": "PS3_functional", "weight": round(w, 3),
                         "detail": f"functional assay deleteriousness {functional_score}"})
    if segregation is True:
        score += 0.15
        evidence.append({"rule": "PP1_segregation", "weight": 0.15,
                         "detail": "co-segregates with disease in family"})
    elif segregation is False:
        score -= 0.1
        evidence.append({"rule": "BS4_nonsegregation", "weight": -0.1,
                         "detail": "does not co-segregate with disease"})

    score = max(0.0, min(1.0, score))
    cls = ("pathogenic" if score >= 0.9 else "likely_pathogenic" if score >= 0.7
           else "uncertain_significance" if score >= 0.35 else
           "likely_benign" if score >= 0.15 else "benign")
    return _result(gene, variant, consequence, cls, round(abs(score - 0.35) / 0.65, 3), evidence)


def _result(gene, variant, consequence, cls, confidence, evidence, curated_note=None):
    return {
        "gene": gene, "variant": variant, "consequence": consequence,
        "classification": cls, "confidence": round(confidence, 3),
        "evidence": evidence, "curated_note": curated_note,
        "plain_language": _plain(gene, variant, consequence, cls),
    }


def _plain(gene: str, variant: str, consequence: str, cls: str) -> str:
    cons_plain = {
        "nonsense": "introduces an early stop signal that truncates the protein",
        "frameshift": "shifts the reading frame, scrambling the protein from this point",
        "missense": "swaps one amino-acid building block for another",
        "synonymous": "changes the DNA spelling but not the protein",
        "splice_disruption": "disrupts how the gene's message is cut and joined",
    }.get(consequence, f"causes a {consequence} change")
    cls_plain = {
        "pathogenic": "is expected to cause disease",
        "likely_pathogenic": "probably causes disease",
        "uncertain_significance": "cannot yet be called harmful or harmless",
        "likely_benign": "is probably harmless",
        "benign": "is considered harmless",
        "risk_factor": "raises risk but does not by itself cause disease",
    }[cls]
    return f"In gene {gene}, variant {variant} {cons_plain}. Current evidence says it {cls_plain}."


def clinical_summary(gene: str, variant: str, **kwargs) -> dict:
    """Patient-friendly report + comparative analysis against curated records."""
    r = interpret_variant(gene, variant, **kwargs)
    comparisons = []
    for (g, v), (cls, why) in KNOWN.items():
        if g == gene:
            comparisons.append({"variant": v, "classification": cls, "note": why})
    return {
        **r,
        "patient_report": {
            "headline": r["plain_language"],
            "what_it_means": ("Discuss targeted screening and family testing with a genetics professional."
                              if r["classification"] in ("pathogenic", "likely_pathogenic")
                              else "No immediate clinical action is indicated from this variant alone."),
            "caveats": "This is computational interpretation support, not a diagnosis.",
        },
        "same_gene_reference_variants": comparisons,
    }
