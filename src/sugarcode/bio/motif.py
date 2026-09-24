"""DNA motif toolkit: PWMs from alignments or IUPAC consensus, log-odds
scoring, two-strand scanning, JASPAR matrix I/O.

PROVENANCE (scoring model):
- Log-odds position weight matrix scoring: Berg OG & von Hippel PH.
  "Selection of DNA binding sites by regulatory proteins." J Mol Biol 1987,
  193:723-750 (statistical-mechanical basis of the specificity/log-odds
  matrix); Stormo GD. "DNA binding sites: representation and discovery."
  Bioinformatics 2000, 16:16-23 (frequency matrix + pseudocount practice).
- score(site) = sum_i log2( p_i(base) / background ), Laplace-style
  pseudocount added to every base count before normalization; a site is
  ranked by its score relative to the matrix's [min, max] score range
  (Wasserman WW & Sandelin A. Nat Rev Genet 2004, 5:276-287).
- JASPAR matrix format: Rauluseviciute I et al. "JASPAR 2024." Nucleic
  Acids Res 2024, 52(D1):D174-D182 - the 4-row A/C/G/T bracketed profile
  layout parsed and written here.

Composes with bio.pwm (the shared low-level PWM functions); this module
adds IUPAC-consensus construction, strand-aware scanning, thresholds and
JASPAR I/O.
"""
from __future__ import annotations

import math

from .pwm import build_pwm, log_odds_matrix, max_score, min_score, score
from .primer import revcomp

BASES = "ACGT"
IUPAC = {"A": "A", "C": "C", "G": "G", "T": "T",
         "R": "AG", "Y": "CT", "S": "GC", "W": "AT", "K": "GT", "M": "AC",
         "B": "CGT", "D": "AGT", "H": "ACT", "V": "ACG", "N": "ACGT"}


def from_alignment(seqs: list[str], *, pseudocount: float = 0.5,
                   background: float = 0.25,
                   name: str | None = None) -> dict:
    """Motif from a gapless alignment of binding sites."""
    pwm = build_pwm(seqs, pseudocount)
    lod = log_odds_matrix(pwm, background)
    return {"name": name or "motif", "length": len(pwm), "pwm": pwm,
            "lod": lod, "background": background,
            "min_score": min_score(lod), "max_score": max_score(lod)}


def from_iupac(consensus: str, *, background: float = 0.25,
               name: str | None = None) -> dict:
    """Motif from an IUPAC degenerate consensus: each position's allowed
    bases get uniform probability."""
    consensus = consensus.upper().strip()
    if not consensus:
        raise ValueError("empty consensus")
    pwm = []
    for ch in consensus:
        if ch not in IUPAC:
            raise ValueError(f"invalid IUPAC code {ch!r}")
        allowed = IUPAC[ch]
        pwm.append({b: (1.0 / len(allowed) if b in allowed else 0.0)
                    for b in BASES})
    lod = log_odds_matrix(pwm, background)
    return {"name": name or consensus, "length": len(pwm), "pwm": pwm,
            "lod": lod, "background": background,
            "min_score": min_score(lod), "max_score": max_score(lod)}


def iupac_consensus(motif: dict) -> str:
    """Degenerate consensus from the PWM: bases within 50% of the column
    maximum join the degenerate code (documented, deterministic rule)."""
    inv = {"".join(sorted(v)): k for k, v in IUPAC.items()}
    out = []
    for col in motif["pwm"]:
        top = max(col.values())
        keep = "".join(sorted(b for b in BASES if col[b] >= 0.5 * top))
        out.append(inv[keep])
    return "".join(out)


def score_site(site: str, motif: dict) -> float:
    return score(site, motif["lod"])


def threshold_score(motif: dict, fraction: float = 0.8) -> float:
    """Score cutoff at `fraction` of the matrix's score range above its
    minimum (Wasserman & Sandelin-style relative threshold)."""
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("fraction must be in [0, 1]")
    return (motif["min_score"]
            + fraction * (motif["max_score"] - motif["min_score"]))


def scan(seq: str, motif: dict, *, threshold: float | None = None,
         threshold_fraction: float | None = 0.8,
         both_strands: bool = True) -> list[dict]:
    """All windows at/above the threshold, both strands by default. Exactly
    one of threshold / threshold_fraction may be given. Hits carry 0-based
    half-open coordinates on the INPUT strand; '-' hits are revcomp windows
    mapped back to input coordinates."""
    if threshold is None:
        threshold = threshold_score(motif, threshold_fraction or 0.0)
    elif threshold_fraction is not None:
        raise ValueError("pass threshold OR threshold_fraction, not both")
    seq = seq.upper()
    L = motif["length"]
    if len(seq) < L:
        return []
    hits = []
    strands = [("+", seq)]
    if both_strands:
        strands.append(("-", revcomp(seq)))
    for strand, s in strands:
        for i in range(len(s) - L + 1):
            sc = score(s[i:i + L], motif["lod"])
            if sc >= threshold:
                if strand == "+":
                    start = i
                else:
                    start = len(seq) - i - L
                hits.append({"start": start, "end": start + L,
                             "strand": strand, "score": round(sc, 4),
                             "matched": s[i:i + L]})
    hits.sort(key=lambda h: -h["score"])
    return hits


def best_hit(seq: str, motif: dict, *, both_strands: bool = True) -> dict:
    hits = scan(seq, motif, threshold=min_score(motif["lod"]),
                threshold_fraction=None, both_strands=both_strands)
    if not hits:
        raise ValueError("sequence shorter than motif")
    return hits[0]


# ------------------------------------------------------------ JASPAR ----

def read_jaspar(text: str, *, pseudocount: float = 0.5,
                background: float = 0.25) -> list[dict]:
    """Parse JASPAR profile matrices (">ID NAME" + 4 A/C/G/T rows, values
    optionally bracketed) into count-based motifs."""
    motifs: list[dict] = []
    header, rows = None, {}
    for ln, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if not s:
            continue
        if s.startswith(">"):
            if header is not None:
                motifs.append(_finish_jaspar(header, rows, pseudocount,
                                             background))
            header, rows = s[1:].strip(), {}
            continue
        if header is None:
            raise ValueError(f"line {ln}: matrix row before any header")
        base = s[0].upper()
        if base not in BASES:
            raise ValueError(f"line {ln}: row must start with A/C/G/T")
        vals = s[1:].replace("[", " ").replace("]", " ").split()
        try:
            rows[base] = [float(v) for v in vals]
        except ValueError:
            raise ValueError(f"line {ln}: non-numeric count")
    if header is not None:
        motifs.append(_finish_jaspar(header, rows, pseudocount, background))
    if not motifs:
        raise ValueError("no JASPAR matrices found")
    return motifs


def _finish_jaspar(header, rows, pseudocount, background):
    if set(rows) != set(BASES):
        raise ValueError(f"{header}: need exactly 4 rows A/C/G/T, got "
                         f"{sorted(rows)}")
    n = len(rows["A"])
    if any(len(rows[b]) != n for b in BASES):
        raise ValueError(f"{header}: rows have different lengths")
    pwm = []
    for i in range(n):
        counts = {b: rows[b][i] + pseudocount for b in BASES}
        total = sum(counts.values())
        pwm.append({b: counts[b] / total for b in BASES})
    lod = log_odds_matrix(pwm, background)
    return {"name": header, "length": n, "pwm": pwm, "lod": lod,
            "background": background, "min_score": min_score(lod),
            "max_score": max_score(lod)}


def write_jaspar(motifs: list[dict]) -> str:
    """Write motifs in JASPAR profile format. Frequencies are re-scaled to
    pseudo-counts summing to 100 per column (JASPAR stores integer counts;
    the original count depth is not recoverable from a frequency matrix -
    documented)."""
    out = []
    for m in motifs:
        out.append(f">{m['name']}")
        for b in BASES:
            vals = " ".join(str(int(round(col[b] * 100)))
                            for col in m["pwm"])
            out.append(f"{b}  [ {vals} ]")
    return "\n".join(out) + "\n"
