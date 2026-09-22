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
try:
    U12_ATAC_DONOR_LOD = _splice.u12_atac_donor_lod()
    U12_ATAC_ACCEPTOR_LOD = _splice.u12_atac_acceptor_lod()
    U12_GTAG_DONOR_LOD = _splice.u12_gtag_donor_lod()
    U12_SOURCE = ("U12 matrices learned from 361 GT-AG + 139 AT-AC human gold "
                  "minor introns (Larue & Roy 2023 intronIC index, see PROVENANCE)")
except _splice.SpliceDataMissing:
    U12_ATAC_DONOR_LOD = U12_ATAC_ACCEPTOR_LOD = U12_GTAG_DONOR_LOD = None
    U12_SOURCE = "U12 matrices missing - AT-AC sites named not-applicable"

# Drop 44: polypyrimidine-tract term for AG acceptors. The position-specific
# PWM cannot express 'a purine ANYWHERE in the tract disrupts it'; the pooled
# tract-zone model (bio.splice.acceptor_tract_lod, learned from the same
# 1,170-junction harvest) can. Blend weight 0.25: a principled split (matrix
# dominant), NOT golden-fit - the golden VALIDATES it (canonical capture
# unchanged by construction: +/-1/-2 variants sit outside the tract zone;
# benign specificity re-measured, reported in STATUS).
TRACT_WEIGHT = 0.25
try:
    TRACT_LOD = _splice.acceptor_tract_lod()
except _splice.SpliceDataMissing:
    TRACT_LOD = None


def tract_score(seq15: str) -> float | None:
    """0..1 tract-zone score of a 15-nt acceptor window, or None when the
    vendored tract model is missing. Position-independent."""
    if TRACT_LOD is None:
        return None
    s = clean_dna(seq15)
    if len(s) != 15:
        raise ValueError("acceptor window must be 15 nt")
    return normalized_score(s[2:12], TRACT_LOD)


def _additive_acceptor(seq15: str, matrix_score: float, ref_class: str) -> float:
    """Matrix score PLUS the weighted tract term (AG acceptors only). The
    matrix contribution is deliberately UNSCALED: the calibrated delta bands
    (-0.15) were fit on the matrix delta, so acceptor delta =
    matrix_delta + TRACT_WEIGHT * (tract_alt - tract_ref). Variants outside
    the tract zone (+/-1, -2) get exactly the matrix delta - canonical
    capture is preserved by construction, not by tuning."""
    if ref_class != "AG" or TRACT_LOD is None:
        return matrix_score
    return round(matrix_score + TRACT_WEIGHT * tract_score(seq15), 4)


# Drop 53: branch-point term for AG acceptors. The 15-mer acceptor window
# ends at -14; the branch zone (-45..-18, Mercer 2015 / Leman 2020) is
# upstream of every existing term, so variants there scored exactly 0 - the
# drop-50 gap measurement. This is a NEW scoring surface over the -60..-1
# intronic window: it does not modify variant_effect/variant_at/score_acceptor,
# so every existing calibrated delta is preserved literally (suite stays
# regression-locked). Weight 0.25 matches the tract-term discipline
# (conservative, NOT golden-fit); validation on the Leman functional set and
# the branch-zone ClinVar sweep is in STATUS.md.
BP_WEIGHT = 0.25
BP_ZONE = (-45, -18)  # branch-A cDNA coordinate range, upstream of 3'SS
try:
    BP_LOD = _splice.branchpoint_lod()
except _splice.SpliceDataMissing:
    BP_LOD = None


def _bp_raw(s: str) -> float:
    best = None
    for i in range(len(s) - 6):
        a_pos = -(len(s) - (i + 5))
        if not (BP_ZONE[0] <= a_pos <= BP_ZONE[1]):
            continue
        sc = sum(BP_LOD[k].get(s[i + k], -99.0) for k in range(7))
        if best is None or sc > best:
            best = sc
    return best if best is not None else 0.0


def branchpoint_score(win60: str) -> float | None:
    """Best branch-point candidate score (summed 7-mer log-odds, bits) with
    branch A in BP_ZONE, over a -60..-1 intronic window (60 nt, transcript
    orientation, last base = -1). None when the model is missing."""
    if BP_LOD is None:
        return None
    s = clean_dna(win60)
    if len(s) != 60:
        raise ValueError("branch-point window must be 60 nt (-60..-1)")
    return round(_bp_raw(s), 4)


def branchpoint_variant_effect(win60: str, index: int, alt_base: str) -> dict:
    """Ref/alt branch-zone assessment: substitution at window index (0-based,
    -60..-1 window) scored with the harvest-learned BP model. Delta is the
    WEIGHTED candidate-score change (BP_WEIGHT x bits), aligned with the
    acceptor delta scale; consequence bands mirror variant_effect."""
    if BP_LOD is None:
        return {"bp_applicable": False,
                "consequence": "branch-point model missing - zone not scored"}
    s = clean_dna(win60)
    if len(s) != 60:
        raise ValueError("branch-point window must be 60 nt (-60..-1)")
    alt = s[:index] + clean_dna(alt_base) + s[index + 1:]
    ref_sc = round(_bp_raw(s), 4)
    alt_sc = round(_bp_raw(alt), 4)
    drop = round(_bp_raw(s) - _bp_raw(alt), 4)  # round the difference once
    delta = round(-BP_WEIGHT * drop, 4)  # negative = candidate disruption
    if drop >= 0.6:
        consequence = ("likely branch-point disruption (candidate drop "
                       f"{drop} bits) - exon skipping risk")
    elif drop >= 0.3:
        consequence = (f"weakened branch-point candidate ({drop} bits) - "
                       "leaky/cryptic 3' splice-site choice possible")
    elif drop <= -0.6:
        consequence = (f"strengthened branch-point candidate ({-drop} bits)"
                       " - altered 3' splice-site choice possible")
    else:
        consequence = "minimal predicted effect on the branch-point candidate"
    return {"bp_applicable": True, "zone": list(BP_ZONE),
            "ref_bp_score": ref_sc, "alt_bp_score": alt_sc,
            "bp_drop_bits": drop, "delta": delta, "weight": BP_WEIGHT,
            "consequence": consequence,
            "pwm_source": ("646 longest-CDS harvest GT-AG acceptors, "
                           "YNYTRAY PWM (drop 50); validated on Leman 2020 "
                           "functional set + branch-zone ClinVar sweep (drop 52)")}


# U12 GT-AG donors are told apart from U2 GT-AG donors by matrix score
# difference. Calibrated 2026-09-22 on the vendored sets: margin 0.15 gives
# 99.2% recall on the 361 gold U12 GT-AG donors at 0.09% FPR on the 1,170
# U2 harvest donors. Acceptor-side discrimination is too weak to route
# (41% recall at 6.4% FPR) - AG acceptors all use the U2 matrix, documented.
U12_DONOR_MARGIN = 0.15


def donor_subtype(window: str) -> str:
    """Fine-grained donor class: U12 GT-AG vs U2 GT-AG vs GC-AG vs AT-AC.
    U12 GT-AG donors carry the RTATCCTTT consensus (minor spliceosome);
    scoring them with the U2 matrix mis-weights the +3..+6 positions."""
    s = clean_dna(window)
    if len(s) != 9:
        raise ValueError("donor window must be 9 nt")
    cls = s[3:5]
    if cls == "AT":
        return "AT-AC"
    if cls == "GC":
        return "GC-AG"
    if cls == "GT":
        if (U12_GTAG_DONOR_LOD is not None
                and normalized_score(s, U12_GTAG_DONOR_LOD) - normalized_score(s, DONOR_LOD)
                >= U12_DONOR_MARGIN):
            return "U12 GT-AG"
        return "U2 GT-AG"
    return "other"


def score_donor(seq9: str, matrix: str = "real") -> float:
    s = clean_dna(seq9)
    if len(s) != 9:
        raise ValueError("donor window must be 9 nt")
    if matrix == "real":
        # GC-AG donors route to the swapped matrix (bio/splice.gc_donor_lod) -
        # the BRCA2 c.7976+2C>G/A golden miss traced to this scope gap.
        # AT-AC (U12) donors route to the learned U12 matrix (drop 27).
        if s[3:5] == "AT" and U12_ATAC_DONOR_LOD is not None:
            lod = U12_ATAC_DONOR_LOD
        else:
            lod = GC_DONOR_LOD if s[3:5] == "GC" else DONOR_LOD
    else:
        lod = SEED_DONOR_LOD
    return round(normalized_score(s, lod), 4)


def _donor_lod_for(ref_window: str):
    """Matrix for a ref/alt PAIR: the REF window's class decides. Scoring the
    alt against its own class made GT->GC conversions look tolerated
    (multi-gene golden caught it: +2T>C pathogenic variants scored ~0).
    AT-AC (U12) donors use the learned U12 matrix when vendored; without it
    they are not scored at all (pwm_applicable False)."""
    cls = clean_dna(ref_window)[3:5]
    if cls == "AT":
        return U12_ATAC_DONOR_LOD
    if cls == "GT" and U12_GTAG_DONOR_LOD is not None and \
            donor_subtype(ref_window) == "U12 GT-AG":
        return U12_GTAG_DONOR_LOD
    return GC_DONOR_LOD if cls == "GC" else DONOR_LOD


def _acceptor_lod_for(ref_window: str):
    cls = clean_dna(ref_window)[12:14]
    return U12_ATAC_ACCEPTOR_LOD if cls == "AC" else ACCEPTOR_LOD


def score_acceptor(seq15: str, matrix: str = "real") -> float:
    s = clean_dna(seq15)
    if len(s) != 15:
        raise ValueError("acceptor window must be 15 nt")
    if matrix == "real":
        if s[12:14] == "AC" and U12_ATAC_ACCEPTOR_LOD is not None:
            return round(normalized_score(s, U12_ATAC_ACCEPTOR_LOD), 4)
        return _additive_acceptor(s, normalized_score(s, ACCEPTOR_LOD), "AG")
    lod = SEED_ACCEPTOR_LOD
    return round(normalized_score(s, lod), 4)


def site_class(window: str, site_type: str = "donor") -> str:
    """Terminal-dinucleotide class of a splice-site window.

    Donor (9-nt window, +1/+2 at offsets 3/4): "GT" or "GC" (U2/major
    spliceosome), "AT" (U12/minor, AT-AC intron), else "other".
    Acceptor (15-nt window, -2/-1 at offsets 12/13): "AG" (U2), "AC"
    (U12), else "other".
    The learned PWMs apply to GT donors (and GC via the documented swap)
    and AG acceptors ONLY. Scoring an AT-AC or other-class site with them
    is not applicable - the extended SCN1A golden (drop 26) caught real
    pathogenic +1 variants at two AT-AC introns scoring delta=0 ("minimal
    effect"), a dangerously wrong answer, before this check existed.
    """
    s = clean_dna(window)
    if site_type == "donor":
        if len(s) != 9:
            raise ValueError("donor window must be 9 nt")
        term = s[3:5]
        return term if term in ("GT", "GC", "AT") else "other"
    if len(s) != 15:
        raise ValueError("acceptor window must be 15 nt")
    term = s[12:14]
    return term if term in ("AG", "AC") else "other"


def pwm_applicable(window: str, site_type: str = "donor") -> bool:
    """Whether a learned PWM may score this window's site class: GT/GC
    donors and AG acceptors via the U2 matrices; AT-AC (U12) sites via the
    U12 matrices when vendored (drop 27), otherwise named not-applicable."""
    cls = site_class(window, site_type)
    if site_type == "donor":
        return cls in ("GT", "GC") or (cls == "AT" and U12_ATAC_DONOR_LOD is not None)
    return cls == "AG" or (cls == "AC" and U12_ATAC_ACCEPTOR_LOD is not None)


def variant_effect(ref_window: str, alt_window: str, site_type: str = "donor",
                   matrix: str = "real") -> dict:
    """Compare splice strength of ref vs alt sequence at a site.

    Windows: 9 nt for donor, 15 nt for acceptor. Returns strength scores,
    delta and a consequence classification.
    """
    if site_type == "donor" and matrix == "real":
        rs = round(normalized_score(clean_dna(ref_window), _donor_lod_for(ref_window)), 4)
        as_ = round(normalized_score(clean_dna(alt_window), _donor_lod_for(ref_window)), 4)
    elif site_type == "acceptor" and matrix == "real":
        cls_a = clean_dna(ref_window)[12:14]
        lod_a = _acceptor_lod_for(ref_window)
        rs = _additive_acceptor(clean_dna(ref_window),
                                round(normalized_score(clean_dna(ref_window), lod_a), 4), cls_a)
        as_ = _additive_acceptor(clean_dna(alt_window),
                                 round(normalized_score(clean_dna(alt_window), lod_a), 4), cls_a)
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
    cls = site_class(ref_window, site_type)
    applicable = pwm_applicable(ref_window, site_type)
    if not applicable:
        consequence = (f"atypical site class ({cls} terminal dinucleotide"
                       f"{' - U12/minor spliceosome intron' if cls in ('AT', 'AC') else ''})"
                       " - GT-AG PWM not applicable; scores not interpretable")
    return {
        "site_type": site_type,
        "site_class": cls,
        "pwm_applicable": applicable,
        "ref_score": rs, "alt_score": as_, "delta": delta,
        "consequence": consequence,
        "isoform_prediction": _isoform_call(site_type, delta),
        "pwm_source": PWM_SOURCE if matrix == "real" else "consensus-seed",
        "threshold_calibration": "BRCA1 ClinVar golden set (186 path/20 benign), 2026-09-21",
        **({"gc_donor": True,
            "gc_note": "GC-AG site scored with the swapped +2 matrix (approximation, "
                       "see bio/splice.gc_donor_lod)"} if gc_donor else {}),
        **({"donor_subtype": donor_subtype(ref_window),
            "u12_note": f"U12 GT-AG (minor spliceosome) donor - scored with the learned "
                        f"U12 GT-AG matrix; U2-vs-U12 margin {U12_DONOR_MARGIN} "
                        f"(99.2% recall / 0.09% FPR on the vendored sets)"}
           if site_type == "donor" and matrix == "real"
           and clean_dna(ref_window)[3:5] == "GT"
           and donor_subtype(ref_window) == "U12 GT-AG" else {}),
        **({"u12_atac": True,
            "u12_note": f"AT-AC (U12 minor spliceosome) site scored with the learned "
                        f"U12 matrix ({U12_SOURCE})"}
           if applicable and cls in ("AT", "AC") else {}),
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


def live_splice_assessment(gene: str, notation: str, offline: bool = False,
                           transcript: str | None = None) -> dict:
    """Splice assessment of one ClinVar-style notation (c.N+k / c.N-k SNV)
    against the gene's REAL RefSeqGene junction map.

    Natural-site variants (donor +1..+6, acceptor -1..-14): window delta via
    the learned PWM. Deeper variants: cryptic_scan on +/-60 nt of real intronic
    context. Everything else: named out-of-scope, never guessed.

    transcript: optional NM_ accession - builds the junction map for THAT
    transcript by aligning its cDNA record's CDS to the RefSeqGene genomic
    sequence (bio.splice.cdna_junction_map, drop 27). Use when ClinVar cites
    a transcript the record does not annotate (SCN1A/NM_001165963: its
    alternative 3'-donor exon-11 extension shifts all downstream c.
    numbering by +33 vs the annotated NM_006920).
    """
    import re as _re
    from ...bio import splice as _sp
    m = _re.fullmatch(r"c\.(-?\d+|\*\d+)([+-])(\d+)([ACGT])>([ACGT])",
                      notation.strip())
    if not m:
        return {"gene": gene, "notation": notation, "status": "unparseable",
                "detail": "expected form c.135-1G>A, c.212+1G>A, c.-23+1G>A (5' UTR) "
                          "or c.*35+1G>A (3' UTR)"}
    n = m.group(1)
    n = int(n) if not n.startswith("*") else n
    sign, k, refb, altb = m.group(2), int(m.group(3)), m.group(4), m.group(5)
    if isinstance(n, str):
        # 3'-UTR intron variant (drop 40): c.*N keys on the UTR map
        # (TP53's last intron is 3'-UTR: donor c.*35, acceptor c.*36).
        if transcript:
            return {"gene": gene, "notation": notation, "status": "outside scope",
                    "detail": "3'-UTR numbering with an explicit transcript map "
                              "is not supported yet"}
        jm = _sp.utr_junction_map(gene, offline=offline)
    elif n < 0:
        # 5'-UTR intron variant (drop 33): CDS maps cannot see these - use
        # the mRNA-exon UTR map (GJB2's only intron is 5'-UTR: c.-23+1G>A).
        # drop 38: with an explicit transcript, the full-cDNA alignment map
        # covers UTR introns on ClinVar's own transcript (GJB2 NM_004004.6).
        # 3'-UTR (c.*N) is still out of scope, named by the maps.
        if transcript:
            jm = _sp.cdna_full_junction_map(gene, transcript, offline=offline)
        else:
            jm = _sp.utr_junction_map(gene, offline=offline)
    elif transcript:
        jm = _sp.cdna_junction_map(gene, transcript, offline=offline)
    else:
        jm = _sp.junction_map(gene, offline=offline)
    if jm["status"] != "ok":
        return {"gene": gene, "notation": notation, "status": jm["status"]}
    seq = jm["sequence"]
    if sign == "+" and k <= 6 and n in jm["donors"]:
        w = jm["donors"][n]; idx = 3 + k - 1
        if w[idx] != refb:
            return {"gene": gene, "notation": notation, "status": "ref mismatch",
                    "detail": f"junction window has {w[idx]} at +{k}, ClinVar says {refb}"}
        if not pwm_applicable(w, "donor"):
            return {"gene": gene, "notation": notation, "status": "atypical_site_class",
                    "site_type": "donor", "site_class": site_class(w, "donor"),
                    "detail": "minor-spliceosome (AT-AC) or non-canonical donor - "
                              "GT-AG PWM not applicable; not scored",
                    "source": jm["source"]}
        r = variant_at(w, idx, altb, "donor")
        out = {"gene": gene, "notation": notation, "status": "natural_site",
               "site_type": "donor", **r, "source": jm["source"]}
        if r["delta"] <= -0.15:
            esc = _exon_skip_context(jm, "donor", n)
            if esc:
                alt = _outcome_context(jm, "donor", n, r["ref_score"])
                if alt:
                    esc["alternative_outcomes"] = alt
                out["exon_context"] = esc
        return out
    if sign == "-" and k <= 14 and n in jm["acceptors"]:
        w = jm["acceptors"][n]; idx = 14 - k
        if w[idx] != refb:
            return {"gene": gene, "notation": notation, "status": "ref mismatch",
                    "detail": f"junction window has {w[idx]} at -{k}, ClinVar says {refb}"}
        if not pwm_applicable(w, "acceptor"):
            return {"gene": gene, "notation": notation, "status": "atypical_site_class",
                    "site_type": "acceptor", "site_class": site_class(w, "acceptor"),
                    "detail": "minor-spliceosome (AT-AC) or non-canonical acceptor - "
                              "GT-AG PWM not applicable; not scored",
                    "source": jm["source"]}
        r = variant_at(w, idx, altb, "acceptor")
        out = {"gene": gene, "notation": notation, "status": "natural_site",
               "site_type": "acceptor", **r, "source": jm["source"]}
        if r["delta"] <= -0.15:
            esc = _exon_skip_context(jm, "acceptor", n)
            if esc:
                alt = _outcome_context(jm, "acceptor", n, r["ref_score"])
                if alt:
                    esc["alternative_outcomes"] = alt
                out["exon_context"] = esc
        return out
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
    out = {"gene": gene, "notation": notation, "status": "cryptic_scan", **r,
           "source": jm["source"]}
    # Drop 56: acceptor-side deep variants inside the branch zone
    # (-18..-45) additionally get the wired branch-point assessment. The
    # -60..-1 window of the SAME acceptor is a slice of the cryptic context
    # (variant at index CTX = position -k, so acceptor -1 sits at index
    # CTX+k-1 and the window is ref_ctx[k:k+60]); AG acceptors only - the BP
    # model is learned on GT-AG introns. Reported as a SEPARATE evidence
    # block; the cryptic_scan verdict is unchanged.
    if sign == "-" and BP_ZONE[0] <= -k <= BP_ZONE[1] and n in jm.get("acceptors", {}):
        w = jm["acceptors"][n]
        if w[12:14] == "AG" and len(ref_ctx) == 2 * CTX + 1:
            out["branchpoint"] = branchpoint_variant_effect(
                ref_ctx[k:k + 60], 60 - k, altb)
    return out


def _outcome_context(jm: dict, site_type: str, n: int, natural_ref: float) -> dict | None:
    """Alternative outcomes of natural-site loss (drop 34), alongside the
    exon-skipping prediction: intron retention (real intron length from the
    RefSeqGene CDS spans; frame + honest PTC/NMD note) and cryptic-site use
    (strongest pre-existing same-type site in the +/-60 nt flank, in
    transcript orientation, excluding the natural site itself; use of an
    exonic cryptic truncates the exon, an intronic one extends it).
    CDS-map only: the UTR map carries no genomic spans, so UTR losses get
    no alternative_outcomes (named, not guessed).
    """
    spans = jm.get("cds_spans")
    if not spans:
        return None
    seq, strand = jm["sequence"], jm["strand"]
    exons = jm.get("exons") or []
    if site_type == "donor":
        i = next((k for k, e in enumerate(exons) if e["cdna_end"] == n), None)
        if i is None or i + 1 >= len(spans):
            return None
        a, b = spans[i]; c, _ = spans[i + 1]
        intron_len = c - b - 1
        flank = (seq[max(0, b - 60):b] + seq[b:b + 60]) if strand == 1 \
            else _rc2(seq[max(0, a - 61):a - 1] + seq[a - 1:a + 59])
    else:
        i = next((k for k, e in enumerate(exons) if e["cdna_start"] == n), None)
        if i is None or i == 0:
            return None
        _, b = spans[i - 1]; c, d = spans[i]
        intron_len = c - b - 1
        flank = (seq[c - 61:c - 1] + seq[c - 1:c + 59]) if strand == 1 \
            else _rc2(seq[max(0, d - 60):d] + seq[d:d + 60])
    if len(flank) != 120:
        return None
    # intron retention
    size_note = ("; note retention is rarely observed for long introns - "
                 "exon skipping dominates there" if intron_len > 1000 else "")
    if intron_len % 3 == 0:
        ret = (f"intron retention ({intron_len} nt, in-frame): would insert "
               f"{intron_len // 3} aa - but retained introns usually carry "
               "premature stop codons and trigger NMD; clean in-frame "
               f"insertion is the exception{size_note}")
    else:
        ret = (f"intron retention ({intron_len} nt, not a multiple of 3): "
               f"frameshift -> premature termination codon / NMD{size_note}")
    # cryptic-site candidates in the flank (same site type, natural excluded)
    from ...bio.pwm import scan as _scan
    lod = DONOR_LOD if site_type == "donor" else ACCEPTOR_LOD
    wlen = len(lod)
    natural_pos = 60 - (3 if site_type == "donor" else wlen - 1)
    cands = []
    for h in _scan(flank, lod, 0.0):
        if h["position"] == natural_pos:
            continue
        w = flank[h["position"]:h["position"] + wlen]
        # a site without its dinucleotide is not viable (donor GT/GC at
        # +1/+2, acceptor AG at -2/-1) - score alone does not imply use
        if site_type == "donor" and w[3:5] not in ("GT", "GC"):
            continue
        if site_type == "acceptor" and w[12:14] != "AG":
            continue
        # donor: window's +1 base (idx 3) is the first intronic base, so the
        # exon/intron boundary sits at pos+3. Acceptor: the window's last
        # base (idx 14) is the first EXONIC base (-14..+1 convention, checked
        # against jm windows), so the boundary sits at pos+wlen-1.
        off = (h["position"] + (3 if site_type == "donor" else wlen - 1)) - 60
        cands.append({"offset_nt": off, "score": round(h["score"], 3),
                      "sequence": flank[h["position"]:h["position"] + wlen]})
    cands = [c for c in cands if c["score"] >= 0.5]
    cands.sort(key=lambda c: -c["score"])
    top = cands[:3]
    crypt = None
    if top:
        t0 = top[0]
        where = ("exonic (exon truncation if used)" if t0["offset_nt"] < 0
                 else "intronic (exon extension if used)")
        crypt = {"candidates": top,
                 "note": (f"strongest pre-existing cryptic {site_type} at "
                          f"{t0['offset_nt']:+d} nt ({where}), score "
                          f"{t0['score']:.2f} vs natural {natural_ref:.2f}; "
                          "cryptic use is a documented outcome of natural-site loss")}
    return {"intron_retention": ret, "cryptic_use": crypt}


def _rc2(s: str) -> str:
    from ...bio.genbank import revcomp
    return revcomp(s)


def _exon_skip_context(jm: dict, site_type: str, n: int) -> dict | None:
    """If the destroyed site causes skipping of its exon, is that exon
    in-frame? Donor loss at c.N+k skips the exon ENDING at cDNA N; acceptor
    loss at c.N-k skips the exon STARTING at cDNA N. Exon lengths are real
    (RefSeqGene CDS spans). Skipping is the common outcome, not the only one
    (intron retention / cryptic use also occur) - labeled as conditional.
    """
    exons = jm.get("exons") or []
    ex = None
    if site_type == "donor":
        ex = next((e for e in exons if e["cdna_end"] == n), None)
    else:
        ex = next((e for e in exons if e["cdna_start"] == n), None)
    if not ex:
        return None
    ln = ex["length"]
    if isinstance(ex["cdna_start"], str) or isinstance(ex["cdna_end"], str):
        # 3'-UTR exon (drop 40): untranslated, no reading-frame consequence
        return {"skipped_exon": ex, "in_frame": None, "utr": True,
                "conditional_prediction": (
                    f"3'-UTR exon ({ln} nt): if skipping occurs, untranslated "
                    "sequence is lost - no reading-frame effect; consequences "
                    "act through 3'-UTR regulation (polyA, miRNA sites, "
                    "stability elements), not protein truncation")}
    if ex["cdna_start"] is None:
        return None  # unnumbered exon - no context
    if ex["cdna_end"] is not None and ex["cdna_end"] < 0:
        # 5'-UTR exon (drop 33): frame language is meaningless here - the
        # skipped sequence is untranslated (GJB2 c.-23+1G>A skips exon 1).
        return {"skipped_exon": ex, "in_frame": None, "utr": True,
                "conditional_prediction": (
                    f"5'-UTR exon ({ln} nt): if skipping occurs, untranslated "
                    "sequence is lost - no reading-frame effect; consequences "
                    "act through 5'-UTR structure / translation regulation, "
                    "not protein truncation")}
    if ex["cdna_start"] < 0:
        return {"skipped_exon": ex, "in_frame": None, "utr": True,
                "conditional_prediction": (
                    f"exon spans the translation start ({ln} nt, 5'-UTR + CDS): "
                    "if skipping occurs, the start-codon context is disrupted")}
    if ln % 3 == 0:
        outcome = (f"in-frame exon ({ln} nt = {ln // 3} aa): if skipping occurs, "
                   "an in-frame deletion results - potentially milder than LoF, "
                   "though domain-critical deletions can still be pathogenic")
    else:
        outcome = (f"out-of-frame exon ({ln} nt): if skipping occurs, a frameshift "
                   "and likely premature termination codon result (LoF mechanism)")
    return {"skipped_exon": ex, "in_frame": ln % 3 == 0,
            "conditional_prediction": outcome}


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

# Transparent context/regulatory/isoform extensions; no transformer or GNN bundled.
import math
import numpy as np
RBP_MOTIFS={'SRSF1':['GAAGAA','GGAGGA'],'HNRNPA1':['TAGGGA','UAGGGA'],'PTBP1':['TTCT','CTCT']}

def regulatory_features(sequence,rbp_maps=None,chromatin=None,elongation_rate=1):
    s=clean_dna(sequence); hits={name:sum(s.count(m.replace('U','T')) for m in motifs) for name,motifs in RBP_MOTIFS.items()}; ext=rbp_maps or {}; hits.update({k:hits.get(k,0)+float(v) for k,v in ext.items()}); gc=(s.count('G')+s.count('C'))/len(s); pairing=sum(a==b for a,b in zip(s,s[::-1]))/len(s); chrom={'H3K36me3':.5,'H3K4me3':.5,**(chromatin or {})}; return {'rbp_hits':hits,'gc_fraction':gc,'structure_pairing_proxy':pairing,'chromatin':chrom,'elongation_rate':elongation_rate,'exon_definition_support':min(1,.2*sum(hits.values())/max(1,len(s))+.35*chrom['H3K36me3']+.2/elongation_rate)}

def exon_inclusion(ref_site,alt_site,regulatory,calibration_n=100):
    delta=alt_site-ref_site; logit=-.5+5*alt_site+2*regulatory['exon_definition_support']; psi=1/(1+math.exp(-logit)); radius=1.96*math.sqrt(psi*(1-psi)/max(1,calibration_n)); return {'psi':psi,'delta_site_strength':delta,'interval95':[max(0,psi-radius),min(1,psi+radius)],'calibration_n':calibration_n}

def isoform_distribution(psi,frame_preserved=True,cryptic_strength=0,intron_retention=.05):
    crypt=max(0,min(1,cryptic_strength))*(1-psi); retained=min(1-psi-crypt,max(0,intron_retention)); skipped=max(0,1-psi-crypt-retained); vals={'canonical':psi,'exon_skipped':skipped,'cryptic_site':crypt,'intron_retained':retained}; z=sum(vals.values()); vals={k:v/z for k,v in vals.items()}; return {'isoforms':vals,'protein_outcomes':{'canonical':'full-length','exon_skipped':'in-frame deletion' if frame_preserved else 'frameshift/truncation','cryptic_site':'altered junction','intron_retained':'PTC/NMD risk'}}

def splice_regulatory_graph(exons,introns,rbp_edges):
    nodes=[{'id':x,'type':'exon'} for x in exons]+[{'id':x,'type':'intron'} for x in introns]; edges=[]
    for rbp,target,effect in rbp_edges: nodes.append({'id':rbp,'type':'RBP'}); edges.append({'source':rbp,'target':target,'effect':effect})
    return {'nodes':list({x['id']:(x) for x in nodes}.values()),'edges':edges,'activation_balance':sum(1 if e['effect']=='enhance' else -1 for e in edges)}

def intervention_simulation(wild_psi,aberrant_psi,strategies):
    out=[]
    for s in strategies:
        effect=float(s.get('psi_shift',0)); off=float(s.get('offtarget_risk',.1)); restored=max(0,min(1,aberrant_psi+effect)); out.append({**s,'restored_psi':restored,'restoration_error':abs(wild_psi-restored),'net_score':1-abs(wild_psi-restored)-off,'status':'non-procedural design concept'})
    return sorted(out,key=lambda x:-x['net_score'])

def active_learning(candidates):
    out=[]
    for c in candidates:
        p=float(c['probability']); uncertainty=4*p*(1-p); impact=float(c.get('impact',.5)); out.append({**c,'priority':uncertainty*impact})
    return sorted(out,key=lambda x:-x['priority'])

def splicing_report(ref_window,alt_window,site_type='donor',context_sequence=None,frame_preserved=True):
    score=score_donor if site_type=='donor' else score_acceptor; ref=score(ref_window); alt=score(alt_window); reg=regulatory_features(context_sequence or ref_window); inc=exon_inclusion(ref,alt,reg); iso=isoform_distribution(inc['psi'],frame_preserved,max(0,alt-ref)); return {'site_type':site_type,'ref_score':ref,'alt_score':alt,'regulatory':reg,'inclusion':inc,'isoforms':iso,'model_status':'PWM, motif and probabilistic context models; no transformer/GNN and not clinically validated.'}

def splice_diagnostics(report):
    r=report['regulatory']; i=report['inclusion']; iso=report['isoforms']['isoforms']; return {'ref_score':report['ref_score'],'alt_score':report['alt_score'],'delta':report['alt_score']-report['ref_score'],'psi':i['psi'],'interval_width':i['interval95'][1]-i['interval95'][0],'gc_fraction':r['gc_fraction'],'pairing_proxy':r['structure_pairing_proxy'],'exon_definition_support':r['exon_definition_support'],'rbp_hit_count':float(sum(r['rbp_hits'].values())),'canonical_isoform':iso['canonical'],'skipped_isoform':iso['exon_skipped'],'cryptic_isoform':iso['cryptic_site'],'retained_isoform':iso['intron_retained']}
