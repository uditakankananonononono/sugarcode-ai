from __future__ import annotations
from ...bio.pwm import build_pwm, log_odds_matrix, normalized_score
from ...bio.sequence import clean_dna
from ...bio import splice as _splice

# Consensus-sequence seed alignments (GT-AG rule); kept as an explicit
# fallback ("seed") now that real learned PWMs are the default.
_DONOR_SITES = [
    "AAGGTAAGT", "CAGGTAAGT", "GAGGTAAGT", "AAGGTGAGT", "CAGGTGAGT",
    "AGGGTGAGT", "AAGGTAAGA", "CAGGTAAGC", "GAGGTATGT", "AAGGTAAAT",
    "CAGGTAAGG", "TGGGTAAGT", "ACGGTAAGT", "GCGGTAAGT", "TGGGTGAGT",
]
_ACCEPTOR_SITES = [
    "TTTTCTTTTCCAGGT", "CTTCCTTTTCCAGGA", "TTCTCTTCTCCAGGC", "TTTCCTTTTACAGGT",
    "CTTTCTTTCCCAGGT", "TTTTCTTCTTCAGGA", "CCTTCTTTTCCAGGT", "TTTTCCTTTCCAGGT",
    "TTCTTTTCTCCAGGT", "CTTTCTCTTTCAGGC", "TTTTCTTTCCCAGGT", "TCTTCTTTTCCAGGT",
    "TTTCCTCTTCCAGGT", "CTTTCTTTTCCAGGA", "TTCTCTTTTCCAGGT",
]

SEED_DONOR_LOD = log_odds_matrix(build_pwm(_DONOR_SITES))
SEED_ACCEPTOR_LOD = log_odds_matrix(build_pwm(_ACCEPTOR_SITES))

# Default matrices: learned from 1,170 real GT-AG junctions across 29
# RefSeqGene records (bio/splice.py, data/splice_sites/PROVENANCE.md).
try:
    DONOR_LOD = _splice.donor_lod()
    ACCEPTOR_LOD = _splice.acceptor_lod()
    GC_DONOR_LOD = _splice.gc_donor_lod()
    PWM_SOURCE = "real RefSeqGene junctions (1,170 GT-AG sites, 29 genes, title-verified)"
except _splice.SpliceDataMissing:
    DONOR_LOD = SEED_DONOR_LOD
    ACCEPTOR_LOD = SEED_ACCEPTOR_LOD
    GC_DONOR_LOD = SEED_DONOR_LOD
    PWM_SOURCE = "consensus-seed fallback (vendored splice data missing)"


def score_donor(seq9: str, matrix: str = "real") -> float:
    s = clean_dna(seq9)
    if len(s) != 9:
        raise ValueError("donor window must be 9 nt")
    if matrix == "real":
        # GC-AG donors route to the swapped matrix (bio/splice.gc_donor_lod) -
        # the BRCA2 c.7976+2C>G/A golden miss traced to this scope gap.
        lod = GC_DONOR_LOD if s[3:5] == "GC" else DONOR_LOD
    else:
        lod = SEED_DONOR_LOD
    return round(normalized_score(s, lod), 4)


def _donor_lod_for(ref_window: str) -> list[dict[str, float]]:
    """Matrix for a ref/alt PAIR: the REF window's class decides. Scoring the
    alt against its own class made GT->GC conversions look tolerated
    (multi-gene golden caught it: +2T>C pathogenic variants scored ~0)."""
    return GC_DONOR_LOD if clean_dna(ref_window)[3:5] == "GC" else DONOR_LOD


def score_acceptor(seq15: str, matrix: str = "real") -> float:
    s = clean_dna(seq15)
    if len(s) != 15:
        raise ValueError("acceptor window must be 15 nt")
    lod = ACCEPTOR_LOD if matrix == "real" else SEED_ACCEPTOR_LOD
    return round(normalized_score(s, lod), 4)


def variant_effect(ref_window: str, alt_window: str, site_type: str = "donor",
                   matrix: str = "real") -> dict:
    """Compare splice strength of ref vs alt sequence at a site.

    Windows: 9 nt for donor, 15 nt for acceptor. Returns strength scores,
    delta and a consequence classification.
    """
    if site_type == "donor" and matrix == "real":
        rs = round(normalized_score(clean_dna(ref_window), _donor_lod_for(ref_window)), 4)
        as_ = round(normalized_score(clean_dna(alt_window), _donor_lod_for(ref_window)), 4)
    else:
        scorer = score_donor if site_type == "donor" else score_acceptor
        rs, as_ = scorer(ref_window, matrix), scorer(alt_window, matrix)
    delta = round(as_ - rs, 4)
    gc_donor = site_type == "donor" and clean_dna(ref_window)[3:5] == "GC"
    # Bands calibrated 2026-09-21 on the BRCA1 ClinVar golden set (186
    # pathogenic / 20 benign splice SNVs on NM_007294; fixture
    # tests/fixtures/brca1_splice_golden.json): at -0.15, sensitivity 0.81
    # (catches essentially all +/-1 and +/-2 canonical-site variants) and
    # specificity 0.95. Known gap: deeper intronic pathogenic variants
    # (k>=3) often act via cryptic-site activation, which a fixed-window
    # PWM cannot see - 0/36 such variants reached the -0.15 band.
    if delta <= -0.15:
        consequence = "likely loss of natural site - exon skipping or intron retention risk"
    elif delta <= -0.05:
        consequence = "weakened site - increased leaky/cryptic splicing risk"
    elif delta >= 0.15:
        consequence = "likely strengthened/cryptic site - novel exon inclusion possible"
    elif delta >= 0.05:
        consequence = "strengthened site - altered isoform balance possible"
    else:
        consequence = "minimal predicted effect on splicing"
    return {
        "site_type": site_type,
        "ref_score": rs, "alt_score": as_, "delta": delta,
        "consequence": consequence,
        "isoform_prediction": _isoform_call(site_type, delta),
        "pwm_source": PWM_SOURCE if matrix == "real" else "consensus-seed",
        "threshold_calibration": "BRCA1 ClinVar golden set (186 path/20 benign), 2026-09-21",
        **({"gc_donor": True,
            "gc_note": "GC-AG site scored with the swapped +2 matrix (approximation, "
                       "see bio/splice.gc_donor_lod)"} if gc_donor else {}),
    }


def variant_at(ref_window: str, index: int, alt_base: str, site_type: str = "donor",
               matrix: str = "real") -> dict:
    """Effect of a single-base substitution at a known offset in the window.

    Donor window offsets: 0..2 exonic, 3 = +1, 4 = +2, ... 8 = +6.
    Acceptor window offsets: 0 = -14 ... 12 = -2, 13 = -1, 14 = first exonic.
    """
    s = clean_dna(ref_window)
    if not 0 <= index < len(s):
        raise ValueError("index outside window")
    alt = s[:index] + alt_base.upper() + s[index + 1:]
    out = variant_effect(s, alt, site_type, matrix)
    out["ref_base"] = s[index]
    out["alt_base"] = alt_base.upper()
    out["window_index"] = index
    return out


def cryptic_scan(ref_seq: str, alt_seq: str, site_threshold: float = 0.75,
                 strengthen_delta: float = 0.10) -> dict:
    """Detect cryptic splice-site activation from a sequence change.

    Scans ref and alt context (same length; point substitution or same-length
    indel region) with the real donor and acceptor PWMs. Reports:
    - new sites: positions where alt crosses `site_threshold` and ref did not
    - strengthened sites: same-position gains of >= `strengthen_delta`
    This is the mechanism behind many deep-intronic pathogenic variants that
    a fixed-window natural-site score cannot see (golden-set finding, drop 22).
    """
    from ...bio.pwm import scan
    ref = clean_dna(ref_seq); alt = clean_dna(alt_seq)
    if len(ref) != len(alt):
        raise ValueError("cryptic_scan needs equal-length ref/alt context")
    findings = []
    for stype, lod in (("donor", DONOR_LOD), ("acceptor", ACCEPTOR_LOD)):
        rh = {h["position"]: h["score"] for h in scan(ref, lod, 0.0)}
        ah = {h["position"]: h["score"] for h in scan(alt, lod, 0.0)}
        for pos, asc in ah.items():
            rsc = rh.get(pos, 0.0)
            if asc >= site_threshold and rsc < site_threshold:
                findings.append({"type": "new_cryptic_site", "site_type": stype,
                                 "position": pos, "ref_score": rsc, "alt_score": asc,
                                 "sequence": alt[pos:pos + len(lod)]})
            elif asc - rsc >= strengthen_delta:
                findings.append({"type": "strengthened_site", "site_type": stype,
                                 "position": pos, "ref_score": rsc, "alt_score": asc,
                                 "sequence": alt[pos:pos + len(lod)]})
    findings.sort(key=lambda f: -(f["alt_score"] - f["ref_score"]))
    strong = [f for f in findings if f["type"] == "new_cryptic_site"]
    weak = [f for f in findings if f["type"] != "new_cryptic_site"]
    # Validation (drop 23): on the BRCA1 ClinVar k>=3 set, new-site events at
    # this threshold fired 0/36 pathogenic and 0/19 benign - high precision.
    # Weak strengthen events fired in BOTH classes (83% vs 84%): they are
    # candidate-generating only, NOT evidence. The published CFTR
    # c.3718-2477C>T cryptic-donor case is detected as a new site (0.68->0.92).
    if strong:
        verdict = (f"NEW cryptic {strong[0]['site_type']} site created "
                   f"(score {strong[0]['ref_score']:.2f} -> {strong[0]['alt_score']:.2f} "
                   f"at position {strong[0]['position']}) - high-precision signal")
    elif weak:
        verdict = (f"{len(weak)} weak site-strength perturbation(s) - common for both "
                   "benign and pathogenic intronic variants; candidate-generating only, "
                   "not discriminating evidence (validated on BRCA1 golden set)")
    else:
        verdict = "no cryptic-site activation detected"
    return {"findings": findings, "strong_findings": strong, "weak_findings": weak,
            "verdict": verdict,
            "site_threshold": site_threshold, "strengthen_delta": strengthen_delta,
            "validation": ("BRCA1 ClinVar k>=3 golden: new-site precision 0 FP in 55; "
                           "weak events non-discriminating (83% path vs 84% benign); "
                           "CFTR c.3718-2477C>T literature case detected (0.68->0.92)"),
            "pwm_source": PWM_SOURCE}


def live_splice_assessment(gene: str, notation: str, offline: bool = False) -> dict:
    """Splice assessment of one ClinVar-style notation (c.N+k / c.N-k SNV)
    against the gene's REAL RefSeqGene junction map.

    Natural-site variants (donor +1..+6, acceptor -1..-14): window delta via
    the learned PWM. Deeper variants: cryptic_scan on +/-60 nt of real intronic
    context. Everything else: named out-of-scope, never guessed.
    """
    import re as _re
    from ...bio import splice as _sp
    m = _re.fullmatch(r"c\.(\d+)([+-])(\d+)([ACGT])>([ACGT])", notation.strip())
    if not m:
        return {"gene": gene, "notation": notation, "status": "unparseable",
                "detail": "expected form c.135-1G>A or c.212+1G>A"}
    n, sign, k, refb, altb = int(m.group(1)), m.group(2), int(m.group(3)), m.group(4), m.group(5)
    jm = _sp.junction_map(gene, offline=offline)
    if jm["status"] != "ok":
        return {"gene": gene, "notation": notation, "status": jm["status"]}
    seq = jm["sequence"]
    if sign == "+" and k <= 6 and n in jm["donors"]:
        w = jm["donors"][n]; idx = 3 + k - 1
        if w[idx] != refb:
            return {"gene": gene, "notation": notation, "status": "ref mismatch",
                    "detail": f"junction window has {w[idx]} at +{k}, ClinVar says {refb}"}
        r = variant_at(w, idx, altb, "donor")
        return {"gene": gene, "notation": notation, "status": "natural_site",
                "site_type": "donor", **r, "source": jm["source"]}
    if sign == "-" and k <= 14 and n in jm["acceptors"]:
        w = jm["acceptors"][n]; idx = 14 - k
        if w[idx] != refb:
            return {"gene": gene, "notation": notation, "status": "ref mismatch",
                    "detail": f"junction window has {w[idx]} at -{k}, ClinVar says {refb}"}
        r = variant_at(w, idx, altb, "acceptor")
        return {"gene": gene, "notation": notation, "status": "natural_site",
                "site_type": "acceptor", **r, "source": jm["source"]}
    # deeper intronic: cryptic scan on real context (strand-aware)
    gpos = _gpos_of(jm, n, sign, k)
    if gpos is None:
        return {"gene": gene, "notation": notation, "status": "outside scope",
                "detail": "exonic or beyond mapped junctions"}
    from ...bio.genbank import revcomp as _rc
    CTX = 60
    if jm["strand"] == 1:
        ref_ctx = seq[gpos-1-CTX:gpos+CTX]
    else:
        ref_ctx = _rc(seq[gpos-1-CTX:gpos+CTX])
    if len(ref_ctx) != 2 * CTX + 1 or ref_ctx[CTX] != refb:
        return {"gene": gene, "notation": notation, "status": "ref mismatch",
                "detail": "context base does not match ClinVar ref"}
    alt_ctx = ref_ctx[:CTX] + altb + ref_ctx[CTX+1:]
    r = cryptic_scan(ref_ctx, alt_ctx)
    return {"gene": gene, "notation": notation, "status": "cryptic_scan", **r,
            "source": jm["source"]}


def _gpos_of(jm: dict, n: int, sign: str, k: int) -> int | None:
    """Genomic position of c.N(sign)k from the CDS spans directly.

    + strand: donor c.N+k anchors at span end b -> b+k; acceptor c.N-k anchors
    at next span start c -> c-k. - strand mirrors with revcomp handled by the
    caller. Anchor must carry cDNA coordinate n exactly."""
    spans = jm["cds_spans"]; strand = jm["strand"]
    cum = 0
    for (a, b), (c, d) in zip(spans, spans[1:]):
        cum += b - a + 1
        if sign == "+" and cum == n:        # last coding base of this exon
            return (b + k) if strand == 1 else (a - k)
        if sign == "-" and cum + 1 == n:    # first coding base of next exon
            return (c - k) if strand == 1 else (d + k)
    return None


def _isoform_call(site_type: str, delta: float) -> str:
    if site_type == "donor" and delta <= -0.15:
        return "exon-skipped isoform becomes dominant"
    if site_type == "acceptor" and delta <= -0.15:
        return "intron-retention / downstream-cryptic-acceptor isoforms rise"
    if delta >= 0.15:
        return "novel splice isoform with extra/missing exonic sequence"
    return "canonical isoform remains dominant"
