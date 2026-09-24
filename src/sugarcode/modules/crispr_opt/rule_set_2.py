"""Rule Set 2 (Azimuth V3) on-target CRISPR guide efficiency scoring.

This is a portable, dependency-light port of the published model from

    Fusi N*, Doench JG* et al. (2016) "In vivo high-throughput profiling of
    CRISPR-Cas9 activity" (code: https://github.com/MicrosoftResearch/Azimuth,
    BSD-3-Clause, (c) Microsoft).

The original ships a scikit-learn 0.17 pickled GradientBoostingRegressor that
cannot be loaded on modern stacks (this gap was listed under "Missing" in
STATUS.md). Here the trained model (100 depth-3 regression trees over 630
sequence/gene-position features) is extracted from the pickle into
framework-free JSON (data/rule_set_2_model.json) and evaluated with a small
pure-NumPy tree-walking engine, so the published model runs anywhere.

Fidelity: predictions reproduce Microsoft's own saved-model regression fixture
(azimuth/tests/1000guides.csv, 947 synthetic guides with reference scores)
with max abs error 5.1e-10 for both the full model (gene-position features)
and the nopos model - far inside Microsoft's own 1e-3 test tolerance. The
feature layout reproduces two quirks of the original Python 2.7 / pandas
pipeline, verified empirically against the fixture:

- the feature-block order is the CPython 2.7 dict iteration order of the
  original featurizer (checked against a real CPython 2.7.18 interpreter);
- the NGGX one-hot columns are in lexicographic dinucleotide order because
  the original pandas concat path sorted string feature labels.

Melting-temperature features are computed with a self-contained
reimplementation of the SantaLucia (1998) unified nearest-neighbor model
exactly as parametrized by Biopython's Tm_staluc/Tm_NN defaults
(DNA_NN3 table, dnac1=dnac2=25 nM, Na=50 mM, salt correction method 5),
verified bit-for-bit against Biopython 1.66/1.79 on the fixture sequences.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np

_MODEL_PATH = os.path.join(os.path.dirname(__file__), "data", "rule_set_2_model.json")
_MODEL = None

ALPHABET_1 = ["A", "T", "C", "G"]
ALPHABET_2 = [a + b for a in ALPHABET_1 for b in ALPHABET_1]
ALPHABET_2_LEX = [a + b for a in "ACGT" for b in "ACGT"]

# SantaLucia (1998) unified DNA/DNA nearest-neighbor parameters, identical to
# Biopython's DNA_NN3 table (Allawi & SantaLucia 1997, Biochemistry 36:10581).
DNA_NN3 = {
    "init": (0.0, 0.0), "init_A/T": (2.3, 4.1), "init_G/C": (0.1, -2.8),
    "init_oneG/C": (0.0, 0.0), "init_allA/T": (0.0, 0.0), "init_5T/A": (0.0, 0.0),
    "sym": (0.0, -1.4),
    "AA/TT": (-7.9, -22.2), "AT/TA": (-7.2, -20.4), "TA/AT": (-7.2, -21.3),
    "CA/GT": (-8.5, -22.7), "GT/CA": (-8.4, -22.4), "CT/GA": (-7.8, -21.0),
    "GA/CT": (-8.2, -22.2), "CG/GC": (-10.6, -27.2), "GC/CG": (-9.8, -24.4),
    "GG/CC": (-8.0, -19.9),
}
_COMPLEMENT = str.maketrans("ACGT", "TGCA")
_R = 1.987  # universal gas constant, cal/(K mol)


def tm_staluc(seq: str, dnac: float = 50.0, saltc: float = 50.0) -> float:
    """DNA/DNA melting temperature via nearest-neighbor thermodynamics.

    Reimplements Biopython's Tm_staluc(s, dnac=50, saltc=50, rna=0), i.e.
    Tm_NN with the DNA_NN3 (SantaLucia 1998 unified) table, dnac1=dnac2=dnac/2
    nM, Na=saltc mM and salt correction method 5 (entropy correction
    0.368*(N-1)*ln[Na+]). Validated against Biopython 1.66 and 1.79 to 0.0 K
    difference on the 3,788 sequences of the Azimuth fixture (947 guides x 4
    Tm segments) plus randomized edge cases (all-A/T, single G/C, 5'-T).
    """
    seq = str(seq).upper()
    if not seq or any(b not in "ACGT" for b in seq):
        raise ValueError("tm_staluc expects a non-empty ACGT sequence, got %r" % seq)
    cseq = seq.translate(_COMPLEMENT)
    d_h, d_s = DNA_NN3["init"]
    gc = seq.count("G") + seq.count("C")
    if gc == 0:
        h, s = DNA_NN3["init_allA/T"]
    else:
        h, s = DNA_NN3["init_oneG/C"]
    d_h += h
    d_s += s
    if seq.startswith("T"):
        h, s = DNA_NN3["init_5T/A"]
        d_h += h
        d_s += s
    if seq.endswith("A"):
        h, s = DNA_NN3["init_5T/A"]
        d_h += h
        d_s += s
    ends = seq[0] + seq[-1]
    n_at = ends.count("A") + ends.count("T")
    n_gc = ends.count("G") + ends.count("C")
    d_h += DNA_NN3["init_A/T"][0] * n_at
    d_s += DNA_NN3["init_A/T"][1] * n_at
    d_h += DNA_NN3["init_G/C"][0] * n_gc
    d_s += DNA_NN3["init_G/C"][1] * n_gc
    for i in range(len(seq) - 1):
        key = seq[i : i + 2] + "/" + cseq[i : i + 2]
        if key in DNA_NN3:
            h, s = DNA_NN3[key]
        else:
            h, s = DNA_NN3[key[::-1]]
        d_h += h
        d_s += s
    k = (dnac / 2.0 - (dnac / 2.0) / 2.0) * 1e-9
    # salt correction method 5 (entropy term), monovalent ions in mol/L
    mon = saltc * 1e-3
    d_s += 0.368 * (len(seq) - 1) * math.log(mon)
    return (1000.0 * d_h) / (d_s + _R * math.log(k)) - 273.15


def _load_model():
    global _MODEL
    if _MODEL is None:
        with open(_MODEL_PATH) as fh:
            _MODEL = json.load(fh)
    return _MODEL


def _blocks(mer30: str) -> dict:
    """Feature blocks for one 30mer (4 nt 5' flank + 20 nt guide + NGG + 3 nt)."""
    s = mer30
    b = {}
    b["pd_order1"] = np.array(
        [1.0 if s[p] == x else 0.0 for p in range(30) for x in ALPHABET_1])
    b["pi_order1"] = np.array([float(s.count(x)) for x in ALPHABET_1])
    b["pd_order2"] = np.array(
        [1.0 if s[p : p + 2] == d else 0.0 for p in range(29) for d in ALPHABET_2])
    di = [s[p : p + 2] for p in range(29)]
    b["pi_order2"] = np.array([float(di.count(d)) for d in ALPHABET_2])
    gc = sum(1 for ch in s[4:24] if ch in "GC")
    b["gc_count"] = np.array([float(gc)])
    b["gc_above_10"] = np.array([1.0 if gc > 10 else 0.0])
    b["gc_below_10"] = np.array([1.0 if gc < 10 else 0.0])
    nx = s[24] + s[27]
    # lexicographic column order: reproduces the label sorting in the original
    # pandas-concat NGGX featurization path
    b["nggx_lex"] = np.array([1.0 if nx == d else 0.0 for d in ALPHABET_2_LEX])
    b["tm"] = np.array([
        tm_staluc(s),
        tm_staluc(s[19:24]),
        tm_staluc(s[11:19]),
        tm_staluc(s[6:11]),
    ])
    return b


def featurize(mer30: str, percent_peptide=None, aa_cut=None, pam_audit: bool = True) -> np.ndarray:
    """630-d (or 627-d nopos) feature vector exactly as the published model expects.

    mer30: 30 nt context sequence (4 nt + 20 nt guide + NGG PAM + 3 nt).
    percent_peptide / aa_cut: gene-position annotations; pass both as real
    numbers for the full model, or omit/pass -1 for the nopos model.
    """
    s = str(mer30).upper()
    if len(s) != 30:
        raise ValueError("Rule Set 2 expects a 30mer context sequence, got %d nt" % len(s))
    if any(ch not in "ACGT" for ch in s):
        raise ValueError("Rule Set 2 expects an ACGT 30mer, got %r" % mer30)
    if pam_audit and s[25:27] != "GG":
        raise ValueError("expected an NGG PAM at positions 25-27 of the 30mer, found %s" % s[24:27])
    use_pos = (
        percent_peptide is not None
        and aa_cut is not None
        and float(percent_peptide) != -1
    )
    b = _blocks(s)
    if use_pos:
        layout = _load_model()["feature_layout_full"]
    else:
        layout = _load_model()["feature_layout_nopos"]
    extra = {
        "percent_peptide": np.array([float(percent_peptide) if use_pos else -1.0]),
        "aa_cut": np.array([float(aa_cut) if use_pos else -1.0]),
        "percent_peptide_lt50": np.array(
            [1.0 if (use_pos and float(percent_peptide) < 50) else 0.0]
        ) if use_pos else np.array([0.0]),
    }
    parts = []
    for name in layout:
        if name in b:
            parts.append(b[name])
        else:
            parts.append(extra[name])
    return np.concatenate(parts)


def _predict_trees(model: dict, X: np.ndarray) -> np.ndarray:
    """Gradient boosting prediction: init + lr * sum of tree leaf values."""
    pred = np.full(X.shape[0], model["init"], dtype=np.float64)
    lr = model["learning_rate"]
    for tr in model["trees"]:
        left = np.asarray(tr["left"])
        right = np.asarray(tr["right"])
        feat = np.asarray(tr["feature"])
        thresh = np.asarray(tr["threshold"])
        value = np.asarray(tr["value"])
        node = np.zeros(X.shape[0], dtype=np.int64)
        while True:
            is_leaf = left[node] < 0
            if is_leaf.all():
                break
            go_left = (X[np.arange(X.shape[0]), feat[node]] <= thresh[node]) & ~is_leaf
            node = np.where(is_leaf, node, np.where(go_left, left[node], right[node]))
        pred = pred + lr * value[node]
    return pred


def score_guides(mer30s, percent_peptides=None, aa_cuts=None, pam_audit: bool = True) -> np.ndarray:
    """Rule Set 2 efficiency scores for a list of 30mers (higher = more active).

    The score is the published model's rank-transformed activity estimate in
    roughly [0, 1]. With percent_peptides and aa_cuts (per-guide, real valued)
    the full V3 model is used; without them the V3-nopos model (627 features)
    is used, mirroring the original library's model selection.
    """
    model = _load_model()
    use_pos = percent_peptides is not None and aa_cuts is not None
    if use_pos and (np.any(np.asarray(percent_peptides, dtype=float) == -1)):
        use_pos = False
    key = "full" if use_pos else "nopos"
    X = np.stack([
        featurize(
            m,
            percent_peptide=(percent_peptides[i] if use_pos else None),
            aa_cut=(aa_cuts[i] if use_pos else None),
            pam_audit=pam_audit,
        )
        for i, m in enumerate(mer30s)
    ])
    return _predict_trees(model[key], X)


def score_guide(mer30: str, percent_peptide=None, aa_cut=None, pam_audit: bool = True) -> float:
    """Rule Set 2 score for a single 30mer context sequence."""
    pp = None if percent_peptide is None else [percent_peptide]
    aa = None if aa_cut is None else [aa_cut]
    return float(score_guides([mer30], pp, aa, pam_audit=pam_audit)[0])
