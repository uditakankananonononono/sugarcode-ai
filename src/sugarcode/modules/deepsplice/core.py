from __future__ import annotations
from ...bio.pwm import build_pwm, log_odds_matrix, normalized_score
from ...bio.sequence import clean_dna

# Consensus-sequence seed alignments (GT-AG rule); PWMs learned from these
# representative sites. Donor: 9 nt (-3..+6 around exon|intron boundary).
_DONOR_SITES = [
    "AAGGTAAGT", "CAGGTAAGT", "GAGGTAAGT", "AAGGTGAGT", "CAGGTGAGT",
    "AGGGTGAGT", "AAGGTAAGA", "CAGGTAAGC", "GAGGTATGT", "AAGGTAAAT",
    "CAGGTAAGG", "TGGGTAAGT", "ACGGTAAGT", "GCGGTAAGT", "TGGGTGAGT",
]
# Acceptor: 15 nt (-14..+1, polypyrimidine tract + AG)
_ACCEPTOR_SITES = [
    "TTTTCTTTTCCAGGT", "CTTCCTTTTCCAGGA", "TTCTCTTCTCCAGGC", "TTTCCTTTTACAGGT",
    "CTTTCTTTCCCAGGT", "TTTTCTTCTTCAGGA", "CCTTCTTTTCCAGGT", "TTTTCCTTTCCAGGT",
    "TTCTTTTCTCCAGGT", "CTTTCTCTTTCAGGC", "TTTTCTTTCCCAGGT", "TCTTCTTTTCCAGGT",
    "TTTCCTCTTCCAGGT", "CTTTCTTTTCCAGGA", "TTCTCTTTTCCAGGT",
]

DONOR_LOD = log_odds_matrix(build_pwm(_DONOR_SITES))
ACCEPTOR_LOD = log_odds_matrix(build_pwm(_ACCEPTOR_SITES))


def score_donor(seq9: str) -> float:
    s = clean_dna(seq9)
    if len(s) != 9:
        raise ValueError("donor window must be 9 nt")
    return round(normalized_score(s, DONOR_LOD), 4)


def score_acceptor(seq15: str) -> float:
    s = clean_dna(seq15)
    if len(s) != 15:
        raise ValueError("acceptor window must be 15 nt")
    return round(normalized_score(s, ACCEPTOR_LOD), 4)


def variant_effect(ref_window: str, alt_window: str, site_type: str = "donor") -> dict:
    """Compare splice strength of ref vs alt sequence at a site.

    Windows: 9 nt for donor, 15 nt for acceptor. Returns strength scores,
    delta and a consequence classification.
    """
    scorer, lod = (score_donor, DONOR_LOD) if site_type == "donor" else (score_acceptor, ACCEPTOR_LOD)
    rs, as_ = scorer(ref_window), scorer(alt_window)
    delta = round(as_ - rs, 4)
    if delta <= -0.30:
        consequence = "likely loss of natural site - exon skipping or intron retention risk"
    elif delta <= -0.10:
        consequence = "weakened site - increased leaky/cryptic splicing risk"
    elif delta >= 0.30:
        consequence = "likely strengthened/cryptic site - novel exon inclusion possible"
    elif delta >= 0.10:
        consequence = "strengthened site - altered isoform balance possible"
    else:
        consequence = "minimal predicted effect on splicing"
    return {
        "site_type": site_type,
        "ref_score": rs, "alt_score": as_, "delta": delta,
        "consequence": consequence,
        "isoform_prediction": _isoform_call(site_type, delta),
    }


def _isoform_call(site_type: str, delta: float) -> str:
    if site_type == "donor" and delta <= -0.30:
        return "exon-skipped isoform becomes dominant"
    if site_type == "acceptor" and delta <= -0.30:
        return "intron-retention / downstream-cryptic-acceptor isoforms rise"
    if delta >= 0.30:
        return "novel splice isoform with extra/missing exonic sequence"
    return "canonical isoform remains dominant"
