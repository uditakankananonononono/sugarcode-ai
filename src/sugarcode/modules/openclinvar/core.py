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


def live_lookup(gene: str, retmax: int = 20, offline: bool = False) -> dict:
    """Live ClinVar variant set for a gene, mapped onto the local ACMG-style
    interpretation frame so live data flows through the same report shape."""
    from ...bio import entrez
    variants = entrez.clinvar_variants(gene, retmax=retmax, offline=offline)
    counts = {}
    for v in variants:
        sig = v["significance"] or "uncertain"
        counts[sig] = counts.get(sig, 0) + 1
    pathogenic = [v for v in variants if "athogenic" in (v["significance"] or "")
                  and "Likely" not in v["significance"] and not v["significance"].startswith("Likely benign")]
    return {
        "gene": gene, "source": "NCBI ClinVar (live)",
        "n_variants": len(variants),
        "significance_counts": counts,
        "variants": [{**v, "stars": clinvar_stars(v.get("review_status"))}
                     for v in variants],
        "pathogenic_or_likely": [v for v in variants
                                 if "athogenic" in (v["significance"] or "")],
        "note": "live classification pulled at query time; review_status shown per variant",
    }


# ClinVar review-status star tiers (official 0-4 scale) and the evidence
# weight each tier carries in the trace. 4 = practice guideline,
# 3 = expert panel, 2 = multiple submitters no conflicts, 1 = single
# submitter or conflicting, 0 = no assertion criteria.
STAR_WEIGHT = {4: 1.0, 3: 0.8, 2: 0.6, 1: 0.3, 0: 0.15}
STAR_STRENGTH = {4: "definitive", 3: "strong", 2: "moderate", 1: "supporting", 0: "weak"}


def clinvar_stars(review_status: str | None) -> int:
    """Map a ClinVar review_status string to its official 0-4 star tier."""
    rs = (review_status or "").lower()
    if "no assertion criteria" in rs or "no classification" in rs or "no interpretation" in rs:
        return 0
    if "practice guideline" in rs:
        return 4
    if "expert panel" in rs:
        return 3
    if "multiple submitters" in rs and "no conflicts" in rs:
        return 2
    if "criteria provided" in rs:  # single submitter or conflicting
        return 1
    return 0


def interpret_variant_live(gene: str, variant: str, offline: bool = False,
                           variant_id: str | None = None, **kwargs) -> dict:
    """interpret_variant enriched with the LIVE ClinVar record for this exact
    variant: when ClinVar has a classification, it enters the evidence trace
    with review-status-weighted strength (expert panel > single submitter);
    when it does not, that absence is stated, not papered over."""
    r = interpret_variant(gene, variant, **kwargs)
    # gene-level gnomAD constraint (drop 18): LOF intolerance is real ACMG
    # context for loss-of-function consequences; attached in all code paths.
    from ...bio import entrez, gnomad
    LOF = {"frameshift", "nonsense", "stop_gained", "splice_acceptor", "splice_donor"}
    try:
        c = gnomad.gene_constraint(gene, offline=offline)
        r["gnomad_constraint"] = c
        cons = kwargs.get("consequence", "")
        if c.get("lof_constrained") and cons in LOF:
            r["evidence"].append({
                "rule": "GNOMAD_CONSTRAINT",
                "weight": 0.3,
                "detail": (f"gene strongly LOF-constrained (pLI {c['pli']:.3f}, "
                           f"LOEUF {c['loeuf']:.3f}); {cons} is a LOF consequence"),
            })
        elif cons in LOF:
            r["evidence"].append({
                "rule": "GNOMAD_CONSTRAINT",
                "weight": 0.0,
                "detail": (f"gene not strongly LOF-constrained (LOEUF "
                           f"{(c.get('loeuf') or 0):.3f}); constraint adds no "
                           "pathogenic support here"),
            })
    except Exception as e:
        r["gnomad_constraint"] = {"status": f"lookup failed: {type(e).__name__}: {e}"}
    # gnomAD population frequency as evidence (drop 21, mirrors rarenet panel):
    # common variants are benign evidence; absent is weak pathogenic support.
    if variant_id:
        try:
            f = gnomad.variant_frequency(variant_id, offline=offline)
            r["gnomad_frequency"] = f
            if f.get("present") and (f.get("max_af") or 0) > 0.01:
                r["evidence"].append({"rule": "GNOMAD_FREQUENCY", "weight": -0.8,
                                      "detail": f"common in population (max AF {f['max_af']:.3g}) - too common for a rare-disease cause"})
            elif f.get("present") is False:
                r["evidence"].append({"rule": "GNOMAD_FREQUENCY", "weight": 0.2,
                                      "detail": "absent from gnomAD - consistent with rare (weak support)"})
        except Exception as e:
            r["gnomad_frequency"] = {"status": f"lookup failed: {type(e).__name__}: {e}"}
    # splice evidence (drop 27, mirrors the rarenet panel): natural-site
    # delta on the gene's real RefSeqGene junction map; deep-intronic ->
    # cryptic_scan; AT-AC sites named out-of-scope; weak perturbations add
    # ZERO (BRCA1-validated non-discriminating). Weights are calibrated
    # against the 28-gene golden: 2,405/2,405 canonical U2 sites called
    # loss, benign specificity 85/86.
    import re as _re
    clean = variant.split(":")[-1].replace(" ", "")
    if _re.fullmatch(r"c\.\d+[+-]\d+[ACGT]>[ACGT]", clean):
        try:
            from ..deepsplice import live_splice_assessment
            sa = live_splice_assessment(gene, clean, offline=offline)
            r["splice_assessment"] = {k: v for k, v in sa.items()
                                      if k in ("status", "site_type", "site_class", "delta",
                                               "consequence", "verdict", "source",
                                               "strong_findings", "exon_context")}
            st = sa.get("status")
            if st == "natural_site":
                d = sa["delta"]
                if d <= -0.15:
                    w = 0.4
                    r["evidence"].append({
                        "rule": "SPLICE_PWM_LOSS", "weight": w,
                        "detail": (f"predicted loss of natural {sa['site_type']} site "
                                   f"(delta {d:+.2f} on the RefSeqGene map; 28-gene golden: "
                                   "100% of 2,405 canonical U2 sites called loss)")})
                elif d <= -0.05:
                    r["evidence"].append({
                        "rule": "SPLICE_PWM_WEAKENED", "weight": 0.1,
                        "detail": f"weakened {sa['site_type']} site (delta {d:+.2f}) - leaky/cryptic risk"})
                else:
                    r["evidence"].append({
                        "rule": "SPLICE_PWM", "weight": 0.0,
                        "detail": (f"weak {sa['site_type']}-site perturbation (delta {d:+.2f}) - "
                                   "validated non-discriminating on the golden set; adds no evidence")})
            elif st == "cryptic_scan":
                if sa.get("strong_findings"):
                    r["evidence"].append({
                        "rule": "SPLICE_CRYPTIC_NEW", "weight": 0.3,
                        "detail": sa["verdict"] + " (high-precision signal: 0 FP in 55 on the BRCA1 k>=3 golden)"})
                else:
                    r["evidence"].append({
                        "rule": "SPLICE_CRYPTIC", "weight": 0.0,
                        "detail": sa.get("verdict", "no cryptic activation") +
                                  " - weak perturbations are non-discriminating; adds no evidence"})
            elif st == "atypical_site_class":
                r["evidence"].append({
                    "rule": "SPLICE_SITE_CLASS", "weight": 0.0,
                    "detail": (f"{sa.get('site_class')} terminal dinucleotide - U12/minor "
                               "spliceosome or non-canonical site; GT-AG PWM not applicable "
                               "(named, never mis-scored)")})
            # ref mismatch / outside scope / no map: attached above, no evidence
        except Exception as e:
            r["splice_assessment"] = {"status": f"lookup failed: {type(e).__name__}: {e}"}
    try:
        matched = entrez.clinvar_exact(gene, variant, offline=offline)
    except Exception as e:
        r["clinvar_live"] = {"status": f"lookup failed: {type(e).__name__}: {e}"}
        return r
    # phrase queries can return near-misses: verify the notation truly appears
    needle = variant.split(":")[-1].replace(" ", "")
    matched = [e for e in matched if needle and needle in e["title"].replace(" ", "")]
    if not matched:
        r["clinvar_live"] = {"status": "no live ClinVar entry for this exact variant",
                             "query": f'{gene}[gene] AND "{variant.split(":")[-1]}"'}
        return r
    m = matched[0]
    stars = clinvar_stars(m["review_status"])
    strength = STAR_STRENGTH[stars]
    sig = (m["significance"] or "").lower()
    if "conflicting" in sig or "uncertain" in sig:
        sign = 0.0
    elif "benign" in sig and "pathogenic" not in sig:
        sign = -1.0
    elif "pathogenic" in sig:
        sign = 1.0
    else:
        sign = 0.0
    r["evidence"].append({
        "rule": "CLINVAR_LIVE",
        "weight": round(sign * STAR_WEIGHT[stars], 3),
        "detail": (f"live ClinVar: {m['significance']} "
                   f"({m['review_status'] or 'review status unknown'}; "
                   f"{stars}-star review)"),
    })
    r["clinvar_live"] = {
        "status": "matched", "title": m["title"],
        "significance": m["significance"], "review_status": m["review_status"],
        "stars": stars,
        "evidence_strength_assigned": strength,
        "note": "classification shown alongside model evidence - clinician adjudicates",
    }
    return r
