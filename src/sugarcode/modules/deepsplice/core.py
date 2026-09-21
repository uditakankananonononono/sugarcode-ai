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

# Default matrices: learned from 1,215 real GT-AG junctions across 28
# RefSeqGene records (bio/splice.py, data/splice_sites/PROVENANCE.md).
try:
    DONOR_LOD = _splice.donor_lod()
    ACCEPTOR_LOD = _splice.acceptor_lod()
    PWM_SOURCE = "real RefSeqGene junctions (1,215 GT-AG sites, 28 genes)"
except _splice.SpliceDataMissing:
    DONOR_LOD = SEED_DONOR_LOD
    ACCEPTOR_LOD = SEED_ACCEPTOR_LOD
    PWM_SOURCE = "consensus-seed fallback (vendored splice data missing)"


def score_donor(seq9: str, matrix: str = "real") -> float:
    s = clean_dna(seq9)
    if len(s) != 9:
        raise ValueError("donor window must be 9 nt")
    lod = DONOR_LOD if matrix == "real" else SEED_DONOR_LOD
    return round(normalized_score(s, lod), 4)


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
    scorer = score_donor if site_type == "donor" else score_acceptor
    rs, as_ = scorer(ref_window, matrix), scorer(alt_window, matrix)
    delta = round(as_ - rs, 4)
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


def _isoform_call(site_type: str, delta: float) -> str:
    if site_type == "donor" and delta <= -0.15:
        return "exon-skipped isoform becomes dominant"
    if site_type == "acceptor" and delta <= -0.15:
        return "intron-retention / downstream-cryptic-acceptor isoforms rise"
    if delta >= 0.15:
        return "novel splice isoform with extra/missing exonic sequence"
    return "canonical isoform remains dominant"
