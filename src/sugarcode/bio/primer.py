"""PCR primer toolkit: SantaLucia nearest-neighbor Tm, GC, structure
heuristics, and a primer-pair picker over a target region.

PROVENANCE:
- Nearest-neighbor dH/dS table (DNA_NN4 below): unified DNA NN parameters of
  SantaLucia J Jr. "A unified view of polymer, dumbbell, and oligonucleotide
  DNA nearest-neighbor thermodynamics." PNAS 1998, 95:1460-1465, with the
  terminal/initiation corrections of SantaLucia J Jr & Hicks D. Annu Rev
  Biophys Biomol Struct 2004, 33:415-440. Values vendored verbatim from the
  DNA_NN4 table in Biopython 1.88's Bio.SeqUtils.MeltingTemp, which itself
  vendors the published values.
- Salt correction on entropy: 0.368 x (N-1) x ln[Na+] (M) - SantaLucia 1998.
- Tm formula: Tm = (1000 x dH) / (dS + R x ln(k)) - 273.15, R = 1.987
  cal/(K mol), k = ([primer] - [template]/2) for non-self-complementary
  duplexes, k = [primer] with the symmetry correction for self-complementary
  sequences (SantaLucia 1998).
- Hairpin/self-dimer checks are documented heuristics (max contiguous
  complementarity runs), NOT full thermodynamic folding - stated plainly
  here and in the CLI help; use primer3 for folding thermodynamics.
"""
from __future__ import annotations

import math

_COMP = str.maketrans("ACGT", "TGCA")

# SantaLucia & Hicks 2004 unified DNA NN table (dH kcal/mol, dS cal/(K mol)),
# vendored from Biopython DNA_NN4 (see PROVENANCE).
_NN = {
    "AA/TT": (-7.6, -21.3), "AT/TA": (-7.2, -20.4), "CA/GT": (-8.5, -22.7),
    "CG/GC": (-10.6, -27.2), "CT/GA": (-7.8, -21.0), "GA/CT": (-8.2, -22.2),
    "GC/CG": (-9.8, -24.4), "GG/CC": (-8.0, -19.9), "GT/CA": (-8.4, -22.4),
    "TA/AT": (-7.2, -21.3),
    "init": (0.2, -5.7), "init_A/T": (2.2, 6.9), "init_G/C": (0.0, 0.0),
    "init_allA/T": (0.0, 0.0), "init_oneG/C": (0.0, 0.0),
    "init_5T/A": (0.0, 0.0), "sym": (0.0, -1.4),
}
_R = 1.987  # cal/(K mol)


def _validate(seq: str) -> str:
    seq = seq.upper().strip()
    if len(seq) < 2:
        raise ValueError("sequence too short for NN thermodynamics")
    bad = sorted(set(seq) - set("ACGT"))
    if bad:
        raise ValueError(f"invalid bases {bad} - DNA only (ACGT)")
    return seq


def revcomp(seq: str) -> str:
    return seq.upper().translate(_COMP)[::-1]


def gc_percent(seq: str) -> float:
    seq = _validate(seq)
    return 100.0 * sum(seq.count(b) for b in "GC") / len(seq)


def max_homopolymer(seq: str) -> int:
    seq = _validate(seq)
    best = run = 1
    for a, b in zip(seq, seq[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    return best


def tm_nn(seq: str, *, primer_nm: float = 25.0, template_nm: float = 25.0,
          na_mm: float = 50.0, selfcomp: bool = False) -> float:
    """SantaLucia NN melting temperature (degC) for a perfect-match duplex.

    Defaults match Biopython Tm_NN (dnac1=dnac2=25 nM, Na=50 mM, salt
    correction method 5) so the implementation can be oracle-tested against
    the reference implementation."""
    seq = _validate(seq)
    if primer_nm <= 0 or template_nm < 0 or na_mm <= 0:
        raise ValueError("concentrations must be positive")
    dh, ds = _NN["init"]
    if gc_percent(seq) > 0:
        dh += _NN["init_oneG/C"][0]
        ds += _NN["init_oneG/C"][1]
    else:
        dh += _NN["init_allA/T"][0]
        ds += _NN["init_allA/T"][1]
    if seq.startswith("T") or seq.endswith("A"):
        dh += _NN["init_5T/A"][0]
        ds += _NN["init_5T/A"][1]
    ends = seq[0] + seq[-1]
    at = ends.count("A") + ends.count("T")
    gc = 2 - at
    dh += _NN["init_A/T"][0] * at + _NN["init_G/C"][0] * gc
    ds += _NN["init_A/T"][1] * at + _NN["init_G/C"][1] * gc
    for i in range(len(seq) - 1):
        d = seq[i:i + 2]
        pair = d + "/" + d.translate(_COMP)  # bottom strand 3'->5' below top
        key = pair if pair in _NN else pair[::-1]
        if key not in _NN:
            raise ValueError(f"no NN parameter for {pair}")
        dh += _NN[key][0]
        ds += _NN[key][1]
    k = primer_nm * 1e-9 if selfcomp else (primer_nm - template_nm / 2.0) * 1e-9
    if k <= 0:
        raise ValueError("primer_nm must exceed template_nm / 2")
    if selfcomp:
        dh += _NN["sym"][0]
        ds += _NN["sym"][1]
    ds += 0.368 * (len(seq) - 1) * math.log(na_mm * 1e-3)  # SantaLucia 1998
    return (1000.0 * dh) / (ds + _R * math.log(k)) - 273.15


def max_complement_run(a: str, b: str) -> int:
    """Longest contiguous run where a[i+k] pairs with b[j+k] for some
    alignment of b (given 3'->5', i.e. pre-reversed) against a."""
    best = 0
    for off in range(-len(b) + 1, len(a)):
        run = 0
        for i in range(len(a)):
            j = i - off
            if 0 <= j < len(b) and a[i] == b[j]:
                run += 1
                best = max(best, run)
            else:
                run = 0
    return best


def hairpin_max_stem(seq: str, *, min_loop: int = 3) -> int:
    """Heuristic: longest contiguous intramolecular stem with loop >=
    `min_loop`. Scans every fold point and stem length."""
    seq = _validate(seq)
    best = 0
    n = len(seq)
    for fold in range(2, n - min_loop - 1):
        # arm left of fold pairs with arm right of fold (+loop)
        for loop in range(min_loop, n - fold):
            right = revcomp(seq[fold + loop:])
            best = max(best, _prefix_run(seq[max(0, fold - len(right)):fold],
                                         right))
    return best


def _prefix_run(a: str, b: str) -> int:
    """Longest match between the 3' end of a and the start of b."""
    n = min(len(a), len(b))
    best = 0
    for i in range(n):
        if a[len(a) - 1 - i] == b[i]:
            best += 1
        else:
            break
    return best


def self_dimer_max_run(seq: str) -> dict:
    """Heuristic: align the sequence against its own reverse complement at
    every offset. Returns the longest contiguous complementary run anywhere
    and the longest run involving either 3' end (the polymerase-extension
    risk that matters for dimers)."""
    seq = _validate(seq)
    rc = revcomp(seq)
    best_any = best_3p = 0
    n = len(seq)
    for off in range(-n + 1, n):
        run, run_3p = 0, 0
        for i in range(n):
            j = i - off
            if 0 <= j < n and seq[i] == rc[j]:
                run += 1
            else:
                if run:
                    best_any = max(best_any, run)
                run = 0
        if run:
            best_any = max(best_any, run)
        # 3' involvement: the last base of seq or of rc participates
        for i in range(n):
            j = i - off
            if 0 <= j < n and seq[i] == rc[j]:
                run_3p += 1
            else:
                if run_3p and (i - 1 == n - 1 or (j - 1) == n - 1):
                    best_3p = max(best_3p, run_3p)
                run_3p = 0
        if run_3p:
            best_3p = max(best_3p, run_3p)
    return {"any": best_any, "three_prime": best_3p}


def pick_primers(template: str, region: tuple[int, int], *, n: int = 3,
                 min_len: int = 18, max_len: int = 25,
                 min_tm: float = 57.0, max_tm: float = 63.0,
                 max_tm_diff: float = 2.0, min_gc: float = 40.0,
                 max_gc: float = 60.0, max_product: int = 1000,
                 flank: int = 300, primer_nm: float = 25.0,
                 na_mm: float = 50.0) -> list[dict]:
    """Pick primer pairs flanking `region` (0-based half-open template
    coordinates); the amplicon must contain the region.

    Hard filters: length, Tm window, pair Tm difference, GC window, GC clamp
    (3' base G/C), <=3 G/C in the last 5 3' bases, homopolymer <=4,
    hairpin stem <=4, self-dimer 3' run <=3, product <= max_product.
    Scored by distance of Tm from 60 degC, GC from 50%, and pair Tm match;
    returns the top `n` pairs."""
    template = _validate(template)
    rstart, rend = region
    if not 0 <= rstart < rend <= len(template):
        raise ValueError("region must be 0-based half-open within template")

    def ok_primer(seq):
        gc = gc_percent(seq)
        if not (min_gc <= gc <= max_gc):
            return None
        if max_homopolymer(seq) > 4:
            return None
        if seq[-1] not in "GC":                       # GC clamp
            return None
        if sum(1 for b in seq[-5:] if b in "GC") > 3:  # 3' stability cap
            return None
        if hairpin_max_stem(seq) > 4:
            return None
        if self_dimer_max_run(seq)["three_prime"] > 3:
            return None
        tm = tm_nn(seq, primer_nm=primer_nm, template_nm=0, na_mm=na_mm)
        if not (min_tm <= tm <= max_tm):
            return None
        return {"seq": seq, "tm": tm, "gc": gc}

    fwds, revs = [], []
    lo_f = max(0, rstart - flank)
    for s in range(lo_f, rstart + 1):
        for ln in range(min_len, max_len + 1):
            if s + ln > len(template):
                continue
            p = ok_primer(template[s:s + ln])
            if p:
                fwds.append({**p, "start": s, "end": s + ln})
    hi_r = min(len(template), rend + flank)
    for e in range(rend, hi_r + 1):
        for ln in range(min_len, max_len + 1):
            if e - ln < 0:
                continue
            p = ok_primer(revcomp(template[e - ln:e]))
            if p:
                revs.append({**p, "start": e - ln, "end": e})

    pairs = []
    for f in fwds:
        for r in revs:
            if r["start"] < f["end"] or r["start"] < rstart or f["end"] > rend:
                continue
            size = r["end"] - f["start"]
            if size > max_product or abs(f["tm"] - r["tm"]) > max_tm_diff:
                continue
            score = (abs(f["tm"] - 60) + abs(r["tm"] - 60)
                     + abs(f["tm"] - r["tm"])
                     + abs(f["gc"] - 50) / 10 + abs(r["gc"] - 50) / 10)
            pairs.append({"forward": f, "reverse": r, "product_size": size,
                          "score": round(score, 4)})
    pairs.sort(key=lambda p: p["score"])
    return pairs[:n]
