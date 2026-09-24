"""Protein physicochemical properties (ProtParam-style).

PROVENANCE (tables vendored verbatim from the published source
implementations; papers cited; cross-checked against Biopython 1.88, which
embeds the same published tables - see tests/test_bio_proteinprops.py oracle
tests):

- pKa tables (pI and charge): Bjellqvist B, Hughes GJ, Pasquali C, Paquet N,
  Ravier F, Sanchez JC, Frutiger S, Hochstrasser D. "The focusing positions
  of polypeptides in immobilized pH gradients can be predicted from their
  amino acid sequences." Electrophoresis 1993, 14:1023-1031. The set used by
  ExPASy ProtParam and EMBOSS iep, including the terminal-residue-specific
  N-/C-terminal pKa adjustments.
- Instability dipeptide weights (DIWV, 400 values): Guruprasad K, Reddy BVB,
  Pandit MW. "Correlation between stability of a protein and its dipeptide
  composition." Protein Engineering 1990, 4(2):155-161.
- Kyte-Doolittle hydropathy: Kyte J, Doolittle RF. J Mol Biol 1982,
  157:105-132.
- Extinction coefficients at 280 nm: Gill SC, von Hippel PH. Anal Biochem
  1989, 182:319-326 (Trp 5500, Tyr 1490, cystine 125); Pace CN et al.
  Protein Science 1995, 4:2411-2423.
- Average isotopic amino-acid masses: standard ExPASy/IUPAC average masses;
  peptide mass = sum(residue masses) - (n-1) x water(18.0153).
- Aromaticity: Lobry JR, Gautier C. Nucleic Acids Res 1994, 22:3174-3180
  (relative frequency of Phe+Trp+Tyr).
"""
from __future__ import annotations

_AA20 = "ACDEFGHIKLMNPQRSTVWY"
_WATER = 18.0153

_RESIDUE_MASS = {
    "A": 89.0932, "C": 121.1582, "D": 133.1027, "E": 147.1293, "F": 165.1891,
    "G": 75.0666, "H": 155.1546, "I": 131.1729, "K": 146.1876, "L": 131.1729,
    "M": 149.2113, "N": 132.1179, "P": 115.1305, "Q": 146.1445, "R": 174.201,
    "S": 105.0926, "T": 119.1192, "V": 117.1463, "W": 204.2252, "Y": 181.1885}

_KD = {
    "A": 1.8, "C": 2.5, "D": -3.5, "E": -3.5, "F": 2.8,
    "G": -0.4, "H": -3.2, "I": 4.5, "K": -3.9, "L": 3.8,
    "M": 1.9, "N": -3.5, "P": -1.6, "Q": -3.5, "R": -4.5,
    "S": -0.8, "T": -0.7, "V": 4.2, "W": -0.9, "Y": -1.3}

_DIWV = {
    "AA": 1.0, "AC": 44.94, "AD": -7.49, "AE": 1.0,
    "AF": 1.0, "AG": 1.0, "AH": -7.49, "AI": 1.0,
    "AK": 1.0, "AL": 1.0, "AM": 1.0, "AN": 1.0,
    "AP": 20.26, "AQ": 1.0, "AR": 1.0, "AS": 1.0,
    "AT": 1.0, "AV": 1.0, "AW": 1.0, "AY": 1.0,
    "CA": 1.0, "CC": 1.0, "CD": 20.26, "CE": 1.0,
    "CF": 1.0, "CG": 1.0, "CH": 33.6, "CI": 1.0,
    "CK": 1.0, "CL": 20.26, "CM": 33.6, "CN": 1.0,
    "CP": 20.26, "CQ": -6.54, "CR": 1.0, "CS": 1.0,
    "CT": 33.6, "CV": -6.54, "CW": 24.68, "CY": 1.0,
    "DA": 1.0, "DC": 1.0, "DD": 1.0, "DE": 1.0,
    "DF": -6.54, "DG": 1.0, "DH": 1.0, "DI": 1.0,
    "DK": -7.49, "DL": 1.0, "DM": 1.0, "DN": 1.0,
    "DP": 1.0, "DQ": 1.0, "DR": -6.54, "DS": 20.26,
    "DT": -14.03, "DV": 1.0, "DW": 1.0, "DY": 1.0,
    "EA": 1.0, "EC": 44.94, "ED": 20.26, "EE": 33.6,
    "EF": 1.0, "EG": 1.0, "EH": -6.54, "EI": 20.26,
    "EK": 1.0, "EL": 1.0, "EM": 1.0, "EN": 1.0,
    "EP": 20.26, "EQ": 20.26, "ER": 1.0, "ES": 20.26,
    "ET": 1.0, "EV": 1.0, "EW": -14.03, "EY": 1.0,
    "FA": 1.0, "FC": 1.0, "FD": 13.34, "FE": 1.0,
    "FF": 1.0, "FG": 1.0, "FH": 1.0, "FI": 1.0,
    "FK": -14.03, "FL": 1.0, "FM": 1.0, "FN": 1.0,
    "FP": 20.26, "FQ": 1.0, "FR": 1.0, "FS": 1.0,
    "FT": 1.0, "FV": 1.0, "FW": 1.0, "FY": 33.601,
    "GA": -7.49, "GC": 1.0, "GD": 1.0, "GE": -6.54,
    "GF": 1.0, "GG": 13.34, "GH": 1.0, "GI": -7.49,
    "GK": -7.49, "GL": 1.0, "GM": 1.0, "GN": -7.49,
    "GP": 1.0, "GQ": 1.0, "GR": 1.0, "GS": 1.0,
    "GT": -7.49, "GV": 1.0, "GW": 13.34, "GY": -7.49,
    "HA": 1.0, "HC": 1.0, "HD": 1.0, "HE": 1.0,
    "HF": -9.37, "HG": -9.37, "HH": 1.0, "HI": 44.94,
    "HK": 24.68, "HL": 1.0, "HM": 1.0, "HN": 24.68,
    "HP": -1.88, "HQ": 1.0, "HR": 1.0, "HS": 1.0,
    "HT": -6.54, "HV": 1.0, "HW": -1.88, "HY": 44.94,
    "IA": 1.0, "IC": 1.0, "ID": 1.0, "IE": 44.94,
    "IF": 1.0, "IG": 1.0, "IH": 13.34, "II": 1.0,
    "IK": -7.49, "IL": 20.26, "IM": 1.0, "IN": 1.0,
    "IP": -1.88, "IQ": 1.0, "IR": 1.0, "IS": 1.0,
    "IT": 1.0, "IV": -7.49, "IW": 1.0, "IY": 1.0,
    "KA": 1.0, "KC": 1.0, "KD": 1.0, "KE": 1.0,
    "KF": 1.0, "KG": -7.49, "KH": 1.0, "KI": -7.49,
    "KK": 1.0, "KL": -7.49, "KM": 33.6, "KN": 1.0,
    "KP": -6.54, "KQ": 24.64, "KR": 33.6, "KS": 1.0,
    "KT": 1.0, "KV": -7.49, "KW": 1.0, "KY": 1.0,
    "LA": 1.0, "LC": 1.0, "LD": 1.0, "LE": 1.0,
    "LF": 1.0, "LG": 1.0, "LH": 1.0, "LI": 1.0,
    "LK": -7.49, "LL": 1.0, "LM": 1.0, "LN": 1.0,
    "LP": 20.26, "LQ": 33.6, "LR": 20.26, "LS": 1.0,
    "LT": 1.0, "LV": 1.0, "LW": 24.68, "LY": 1.0,
    "MA": 13.34, "MC": 1.0, "MD": 1.0, "ME": 1.0,
    "MF": 1.0, "MG": 1.0, "MH": 58.28, "MI": 1.0,
    "MK": 1.0, "ML": 1.0, "MM": -1.88, "MN": 1.0,
    "MP": 44.94, "MQ": -6.54, "MR": -6.54, "MS": 44.94,
    "MT": -1.88, "MV": 1.0, "MW": 1.0, "MY": 24.68,
    "NA": 1.0, "NC": -1.88, "ND": 1.0, "NE": 1.0,
    "NF": -14.03, "NG": -14.03, "NH": 1.0, "NI": 44.94,
    "NK": 24.68, "NL": 1.0, "NM": 1.0, "NN": 1.0,
    "NP": -1.88, "NQ": -6.54, "NR": 1.0, "NS": 1.0,
    "NT": -7.49, "NV": 1.0, "NW": -9.37, "NY": 1.0,
    "PA": 20.26, "PC": -6.54, "PD": -6.54, "PE": 18.38,
    "PF": 20.26, "PG": 1.0, "PH": 1.0, "PI": 1.0,
    "PK": 1.0, "PL": 1.0, "PM": -6.54, "PN": 1.0,
    "PP": 20.26, "PQ": 20.26, "PR": -6.54, "PS": 20.26,
    "PT": 1.0, "PV": 20.26, "PW": -1.88, "PY": 1.0,
    "QA": 1.0, "QC": -6.54, "QD": 20.26, "QE": 20.26,
    "QF": -6.54, "QG": 1.0, "QH": 1.0, "QI": 1.0,
    "QK": 1.0, "QL": 1.0, "QM": 1.0, "QN": 1.0,
    "QP": 20.26, "QQ": 20.26, "QR": 1.0, "QS": 44.94,
    "QT": 1.0, "QV": -6.54, "QW": 1.0, "QY": -6.54,
    "RA": 1.0, "RC": 1.0, "RD": 1.0, "RE": 1.0,
    "RF": 1.0, "RG": -7.49, "RH": 20.26, "RI": 1.0,
    "RK": 1.0, "RL": 1.0, "RM": 1.0, "RN": 13.34,
    "RP": 20.26, "RQ": 20.26, "RR": 58.28, "RS": 44.94,
    "RT": 1.0, "RV": 1.0, "RW": 58.28, "RY": -6.54,
    "SA": 1.0, "SC": 33.6, "SD": 1.0, "SE": 20.26,
    "SF": 1.0, "SG": 1.0, "SH": 1.0, "SI": 1.0,
    "SK": 1.0, "SL": 1.0, "SM": 1.0, "SN": 1.0,
    "SP": 44.94, "SQ": 20.26, "SR": 20.26, "SS": 20.26,
    "ST": 1.0, "SV": 1.0, "SW": 1.0, "SY": 1.0,
    "TA": 1.0, "TC": 1.0, "TD": 1.0, "TE": 20.26,
    "TF": 13.34, "TG": -7.49, "TH": 1.0, "TI": 1.0,
    "TK": 1.0, "TL": 1.0, "TM": 1.0, "TN": -14.03,
    "TP": 1.0, "TQ": -6.54, "TR": 1.0, "TS": 1.0,
    "TT": 1.0, "TV": 1.0, "TW": -14.03, "TY": 1.0,
    "VA": 1.0, "VC": 1.0, "VD": -14.03, "VE": 1.0,
    "VF": 1.0, "VG": -7.49, "VH": 1.0, "VI": 1.0,
    "VK": -1.88, "VL": 1.0, "VM": 1.0, "VN": 1.0,
    "VP": 20.26, "VQ": 1.0, "VR": 1.0, "VS": 1.0,
    "VT": -7.49, "VV": 1.0, "VW": 1.0, "VY": -6.54,
    "WA": -14.03, "WC": 1.0, "WD": 1.0, "WE": 1.0,
    "WF": 1.0, "WG": -9.37, "WH": 24.68, "WI": 1.0,
    "WK": 1.0, "WL": 13.34, "WM": 24.68, "WN": 13.34,
    "WP": 1.0, "WQ": 1.0, "WR": 1.0, "WS": 1.0,
    "WT": -14.03, "WV": -7.49, "WW": 1.0, "WY": 1.0,
    "YA": 24.68, "YC": 1.0, "YD": 24.68, "YE": -6.54,
    "YF": 1.0, "YG": -7.49, "YH": 13.34, "YI": 1.0,
    "YK": 1.0, "YL": 1.0, "YM": 44.94, "YN": 1.0,
    "YP": 13.34, "YQ": 1.0, "YR": -15.91, "YS": 1.0,
    "YT": -7.49, "YV": 1.0, "YW": -9.37, "YY": 13.34}

_POS_PKS = {
    "H": 5.98, "K": 10.0, "Nterm": 7.5, "R": 12.0}
_NEG_PKS = {
    "C": 9.0, "Cterm": 3.55, "D": 4.05, "E": 4.45, "Y": 10.0}
_PK_NTERM = {
    "A": 7.59, "E": 7.7, "M": 7.0, "P": 8.36, "S": 6.93,
    "T": 6.82, "V": 7.44}
_PK_CTERM = {
    "D": 4.55, "E": 4.75}

_CHARGED = ("K", "R", "H", "D", "E", "C", "Y")
_EXTINCTION = {"W": 5500, "Y": 1490}
_CYSTINE_EXTINCTION = 125


def _validate(seq: str) -> str:
    seq = seq.upper().strip()
    if not seq:
        raise ValueError("empty sequence")
    bad = sorted(set(seq) - set(_AA20))
    if bad:
        raise ValueError(f"non-standard residues {bad} - only the 20 "
                         f"standard amino acids are supported")
    return seq


def molecular_weight(seq: str) -> float:
    """Average-isotope peptide mass: sum(residues) - (n-1) x 18.0153."""
    seq = _validate(seq)
    return sum(_RESIDUE_MASS[a] for a in seq) - (len(seq) - 1) * _WATER


def extinction_coefficient(seq: str) -> dict:
    """Molar extinction at 280 nm. reduced: all Cys free thiols. oxidized:
    all Cys paired into cystines (125 per PAIR; an odd cysteine is left
    reduced - Gill & von Hippel count cystine, not cysteine)."""
    seq = _validate(seq)
    reduced = sum(seq.count(a) * e for a, e in _EXTINCTION.items())
    oxidized = reduced + (seq.count("C") // 2) * _CYSTINE_EXTINCTION
    return {"reduced": reduced, "oxidized": oxidized}


def instability_index(seq: str) -> float:
    """Guruprasad instability index: (10/n) x sum of dipeptide weights.
    >40 predicts a short half-life in vivo."""
    seq = _validate(seq)
    score = sum(_DIWV[seq[i:i + 2]] for i in range(len(seq) - 1))
    return (10.0 / len(seq)) * score


def aromaticity(seq: str) -> float:
    """Relative frequency (0-1) of Phe+Trp+Tyr (Lobry & Gautier 1994)."""
    seq = _validate(seq)
    return sum(seq.count(a) for a in "FWY") / len(seq)


def gravy(seq: str) -> float:
    """Grand average of hydropathy (Kyte-Doolittle 1982)."""
    seq = _validate(seq)
    return sum(_KD[a] for a in seq) / len(seq)


def _pks(seq: str) -> tuple[dict, dict]:
    pos, neg = _POS_PKS.copy(), _NEG_PKS.copy()
    if seq[0] in _PK_NTERM:
        pos["Nterm"] = _PK_NTERM[seq[0]]
    if seq[-1] in _PK_CTERM:
        neg["Cterm"] = _PK_CTERM[seq[-1]]
    return pos, neg


def charge_at_ph(seq: str, ph: float) -> float:
    """Net charge via Henderson-Hasselbalch partial charges (Bjellqvist
    pKa set, terminal-specific adjustments applied)."""
    seq = _validate(seq)
    if not 0.0 <= ph <= 14.0:
        raise ValueError("pH must be in [0, 14]")
    pos, neg = _pks(seq)
    counts = {a: seq.count(a) for a in _CHARGED}
    counts["Nterm"] = counts["Cterm"] = 1
    positive = sum(counts[a] / (10 ** (ph - pK) + 1.0)
                   for a, pK in pos.items())
    negative = sum(counts[a] / (10 ** (pK - ph) + 1.0)
                   for a, pK in neg.items())
    return positive - negative


def isoelectric_point(seq: str, tol: float = 1e-4) -> float:
    """pI by bisection of charge_at_ph over [4.05, 12] (below/above the
    all-Asp / all-Arg theoretical bounds, per Bjellqvist)."""
    seq = _validate(seq)
    lo, hi = 4.05, 12.0
    ph = (lo + hi) / 2
    while hi - lo > tol:
        if charge_at_ph(seq, ph) > 0.0:
            lo = ph
        else:
            hi = ph
        ph = (lo + hi) / 2
    return ph


def protein_summary(seq: str) -> dict:
    """All properties in one call, rounded for reporting."""
    seq = _validate(seq)
    ext = extinction_coefficient(seq)
    ii = instability_index(seq)
    return {"length": len(seq),
            "molecular_weight": round(molecular_weight(seq), 2),
            "extinction_reduced": ext["reduced"],
            "extinction_oxidized": ext["oxidized"],
            "isoelectric_point": round(isoelectric_point(seq), 2),
            "instability_index": round(ii, 2),
            "instability_prediction": "unstable" if ii > 40 else "stable",
            "aromaticity": round(aromaticity(seq), 4),
            "gravy": round(gravy(seq), 4)}
