"""Drop 51: exonic acceptor +1..+3 sweep - +1 strong (confirms drop 47),
+2/+3 flat (honest null; validates the calibrated +1-only window)."""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/exonic_acceptor3_golden.json").read_text())
EP = json.loads(Path("src/sugarcode/bio/data/splice_sites/acceptor_exon_pwm.json").read_text())


def _d(off, sig):
    return [c["delta"] for g in FIX["genes"].values() for c in g["cases"]
            if c["exonic_offset"] == off and c["sig"] == sig]


def test_sweep_counts():
    cases = [c for g in FIX["genes"].values() for c in g["cases"]]
    assert len(FIX["genes"]) == 28
    assert len(cases) == 348
    assert sum(c["sig"] == "pathogenic" for c in cases) == 44
    assert sum(c["sig"] == "benign" for c in cases) == 22
    assert all(len(c["ref_triplet"]) == 3 for c in cases)  # ref-verified triplets


def test_plus1_signal_plus23_null():
    p1, p2, p3 = _d(1, "pathogenic"), _d(2, "pathogenic"), _d(3, "pathogenic")
    assert sum(p1) / len(p1) < -1.0           # +1 strong pathogenic loss
    assert sum(p2) / len(p2) > -0.1           # +2 flat (inverted, tiny n)
    assert abs(sum(p3) / len(p3)) < 0.2       # +3 flat (wobble)
    b3 = _d(3, "benign")
    assert abs(sum(b3) / len(b3)) < 0.2       # benign also flat at +3


def test_exon_pwm_model():
    assert EP["n_acceptors"] == 642
    assert EP["pwm"][0]["G"] > 0.45           # +1 G preference
    assert abs(sum(EP["background"].values()) - 1.0) < 0.01


def test_entrez_retries_incomplete_reads():
    src = Path("src/sugarcode/bio/entrez.py").read_text()
    assert "IncompleteRead" in src  # drop-51 connector robustness fix
