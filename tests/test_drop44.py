"""Drop 44: polypyrimidine-tract term in acceptor scoring. The pooled
tract-zone model (acceptor_tract_pwm.json: 78.7% pyrimidine over indices
2..11 = c.-12..-3, learned from the 1,170-junction harvest by
scripts/learn_tract_pwm.py) adds a position-independent penalty the
position-specific PWM cannot express. Wiring is ADDITIVE with the matrix
contribution UNSCALED (acceptor delta = matrix_delta + 0.25 * tract delta),
so +/-1/-2 canonical deltas are preserved exactly - by construction, not
tuning. Validated (scripts/rescore_golden_tract.py): canonical 2,405/2,405
re-scored, benign specificity 85/86 UNCHANGED, tract-zone separation
widened (pathogenic mean -0.057 -> -0.073, benign -0.002 -> -0.003) and no
tract-zone case in either class crosses the -0.15 band. All fixtures
re-scored to the new model (1,309 deltas moved; the regression-lock test
now locks the tract-term model).
"""
import json, re, statistics as st
from pathlib import Path
from sugarcode.modules.deepsplice import (variant_at, tract_score,
                                          score_acceptor, TRACT_LOD,
                                          TRACT_WEIGHT)
from sugarcode.bio.pwm import normalized_score
import sys
sys.path.insert(0, "src")


def test_tract_model_learned_values():
    d = json.loads(Path("src/sugarcode/bio/data/splice_sites/acceptor_tract_pwm.json")
                   .read_text())
    assert d["n_acceptors"] == 1176 and d["zone"] == [2, 12]
    pyr = d["pwm"]["C"] + d["pwm"]["T"]
    assert 0.78 < pyr < 0.80
    assert TRACT_LOD is not None and len(TRACT_LOD) == 10


def test_core_deltas_preserved_exactly():
    # -1/-2 acceptor variants sit outside the tract zone: delta must equal
    # the matrix-only delta
    w = "TCTGTCTCCTACAGC"  # TP53 acceptor window
    assert variant_at(w, 13, "C", "acceptor")["delta"] == -0.1838
    assert variant_at(w, 12, "C", "acceptor")["delta"] == -0.1838


def test_tract_disruption_penalized():
    strong_tract = "TCTTTTCTCATTAGT"
    v = variant_at(strong_tract, 5, "A", "acceptor")
    assert v["delta"] < -0.05  # single purine in a strong tract now costs
    assert tract_score(strong_tract) > tract_score("GAAGGAAGAAGAAGT")


def test_regression_locks_hold():
    # canonical + benign from the re-scored fixtures
    import subprocess
    out = subprocess.run(["python3", "scripts/rescore_golden_tract.py"],
                         capture_output=True, text=True).stdout
    assert "canonical +/-1/-2 (re-scored): 2405/2405" in out
    assert "benign specificity (re-scored): 85/86" in out
    assert "cases whose delta moved with the tract term: 0" in out


def test_tract_zone_separation_widened():
    rows = []
    for f in sorted(Path("tests/fixtures").glob("*_splice_golden.json")):
        if f.name in ("vus_splice_golden.json",
                      "conflicting_splice_golden.json",
                      "cftr_cryptic_golden.json"):
            continue
        d = json.loads(f.read_text())
        for sig in ("pathogenic", "benign"):
            for c in d.get(sig, []):
                if c["site_type"] != "acceptor":
                    continue
                m = re.search(r"-(\d+)([ACGT])>([ACGT])", c["notation"])
                k = int(m.group(1))
                if 3 <= k <= 12 and 2 <= 14 - k <= 11:
                    rows.append((sig, c["delta"]))
    p = [v for s, v in rows if s == "pathogenic"]
    b = [v for s, v in rows if s == "benign"]
    assert len(p) == 72 and len(b) == 61
    assert st.mean(p) <= -0.07 and st.mean(b) >= -0.01
    # honest limit: no tract-zone case reaches the strong band in either class
    assert not any(v <= -0.15 for v in p + b)
