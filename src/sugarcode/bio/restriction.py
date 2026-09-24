"""Restriction digest toolkit: recognition-site search (linear/circular),
overhang-aware cuts, fragment lists, gel-migration estimate.

Enzyme data: 610 commercially available enzymes vendored in
bio/data/restriction/enzymes.json - see PROVENANCE.md there (extracted
programmatically from Biopython 1.88 Bio.Restriction, which vendors REBASE;
not hand-typed).

Cut model (Biopython/REBASE convention): for a recognition-site match
starting at position p, the top strand is cut at p + fst5 and the bottom
strand at p + len(site) + fst3 (same coordinates; offsets may fall outside
the site for Type IIS enzymes). cut_bottom - cut_top > 0 => 5' overhang,
< 0 => 3' overhang, = 0 => blunt. For non-palindromic sites the reverse
strand is searched with the revcomp pattern and cut positions mirror.

Gel estimate: relative migration m = a - b x log10(bp), calibrated so a
100 bp band migrates 0.9 and a 10 kb band 0.1 on a notional 1% agarose gel
- an ILLUSTRATIVE standard curve (documented; real mobility depends on gel
%, buffer, voltage), following the usual log-linear DNA-size/mobility
relationship (e.g. Southern EM, Methods Enzymol 1979, 68:152-176).
"""
from __future__ import annotations

import json
import math
import re
from importlib import resources

_IUPAC_COMP = str.maketrans("ACGTRYSWKMBDHVN", "TGCAYRSWMKVHDBN")


def revcomp(seq: str) -> str:
    """IUPAC-aware reverse complement (R<->Y, K<->M, B<->V, D<->H; S, W, N self).
    The plain DNA revcomp left degenerate codes uncomplemented, so degenerate
    sites such as AccI GTMKAC were searched with a wrong reverse pattern."""
    return seq.upper().translate(_IUPAC_COMP)[::-1]

_IUPAC_RE = {"A": "A", "C": "C", "G": "G", "T": "T", "R": "[AG]", "Y": "[CT]",
             "S": "[GC]", "W": "[AT]", "K": "[GT]", "M": "[AC]", "B": "[CGT]",
             "D": "[AGT]", "H": "[ACT]", "V": "[ACG]", "N": "[ACGT]"}

_TABLE = None


def _load() -> dict:
    global _TABLE
    if _TABLE is None:
        with resources.files("sugarcode.bio.data.restriction").joinpath(
                "enzymes.json").open() as fh:
            _TABLE = json.load(fh)
    return _TABLE


def list_enzymes() -> list[str]:
    return sorted(_load())


def enzyme_info(name: str) -> dict:
    table = _load()
    if name not in table:
        raise ValueError(f"unknown enzyme {name!r} ({len(table)} available "
                         f"via list_enzymes())")
    site, fst5, fst3 = table[name]
    cut_bottom = len(site) + fst3
    diff = cut_bottom - fst5
    return {"name": name, "site": site, "cut_top": fst5,
            "cut_bottom": cut_bottom,
            "overhang": ("5'" if diff > 0 else "3'" if diff < 0 else "blunt"),
            "overhang_length": abs(diff),
            "palindromic": site == revcomp(site)}


def find_sites(seq: str, enzyme: str, *, circular: bool = False) -> list[dict]:
    """All recognition-site matches with overhang-aware cut positions."""
    seq = seq.upper()
    info = enzyme_info(enzyme)
    site = info["site"]
    L = len(site)
    patterns = [("+", re.compile("(?=(" + "".join(_IUPAC_RE[c]
                                                 for c in site) + "))"))]
    if not info["palindromic"]:
        rc = revcomp(site)
        patterns.append(("-", re.compile("(?=(" + "".join(_IUPAC_RE[c]
                                                        for c in rc) + "))")))
    n = len(seq)
    hits = []
    for strand, rx in patterns:
        hay = seq + (seq[:L - 1] if circular else "")
        for m in rx.finditer(hay):
            p = m.start()
            if p >= n:
                break
            if strand == "+":
                cut_top, cut_bottom = (p + info["cut_top"],
                                       p + info["cut_bottom"])
            else:
                cut_top = p + L - info["cut_bottom"]
                cut_bottom = p + L - info["cut_top"]
            if circular:
                cut_top %= n
                cut_bottom %= n
            elif not (0 < cut_top < n and 0 < cut_bottom < n):
                continue  # linear DNA: a cut outside the molecule does not happen (Type IIS near the ends)
            hits.append({"enzyme": enzyme, "start": p, "end": p + L,
                         "strand": strand, "cut_top": cut_top,
                         "cut_bottom": cut_bottom,
                         "overhang": info["overhang"],
                         "overhang_length": info["overhang_length"]})
    hits.sort(key=lambda h: h["start"])
    return hits


def digest(seq: str, enzymes: list[str], *, circular: bool = False) -> dict:
    """Fragment sizes from a single- or multi-enzyme digest. Fragment
    boundaries are the TOP-strand cut positions (the physical fragment
    length convention; overhangs are reported per cut but do not change
    lengths)."""
    seq = seq.upper()
    n = len(seq)
    if n == 0:
        raise ValueError("empty sequence")
    cuts = []
    for e in enzymes:
        cuts.extend(find_sites(seq, e, circular=circular))
    positions = sorted({c["cut_top"] for c in cuts})
    if circular:
        if not positions:
            fragments = [n]
        else:
            fragments = ([positions[0] + n - positions[-1]]
                         + [b - a for a, b in zip(positions, positions[1:])])
    else:
        bounds = [0] + [p for p in positions if 0 < p < n] + [n]
        fragments = [b - a for a, b in zip(bounds, bounds[1:])]
    fragments.sort(reverse=True)
    return {"enzymes": list(enzymes), "circular": circular,
            "length": n, "n_sites": len(cuts), "cuts": cuts,
            "fragments": fragments}


def gel_bands(fragment_sizes: list[int]) -> list[dict]:
    """Illustrative relative migration for each fragment (see module
    docstring): m = a - b x log10(bp), a/b set so 100 bp -> 0.9 and
    10 kb -> 0.1. Bands are returned largest-first with co-migrating sizes
    (within 0.5% log) grouped."""
    a, b = 1.7, 0.4          # m(100)=0.9, m(10000)=0.1
    bands = [{"size": s, "log10_bp": round(math.log10(s), 4),
              "rel_migration": round(a - b * math.log10(s), 4)}
             for s in sorted(fragment_sizes, reverse=True)]
    return bands
