"""Drop 52: branch-zone ClinVar sweep - enlarged BP-signal evidence."""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/branchzone_clinvar_golden.json").read_text())


def _bpz(sig):
    return [c["bp_pwm_drop"] for g in FIX["genes"].values() for c in g["cases"]
            if c["in_bp_zone"] and c["sig"] == sig]


def test_sweep_counts():
    cases = [c for g in FIX["genes"].values() for c in g["cases"]]
    assert len(cases) == 1923
    assert sum(s["excluded"] for s in FIX["summary"].values()) == 0
    bpz = [c for c in cases if c["in_bp_zone"]]
    assert len(bpz) == 127
    assert all(18 <= c["dist"] <= 45 for c in bpz)
    # BP zone and tract zone are disjoint by construction
    assert not any(c["in_bp_zone"] and c["in_tract_zone"] for c in cases)


def test_bp_zone_direction():
    p, b = _bpz("pathogenic"), _bpz("benign")
    assert len(p) == 19 and len(b) == 31
    assert sum(p) / len(p) > 0.5            # pathogenic: candidate disruption
    assert sum(b) / len(b) < 0.0            # benign: none on average
    fp = sum(d >= 0.5 for d in p) / len(p)
    fb = sum(d >= 0.5 for d in b) / len(b)
    assert fp > 3 * fb                      # 36.8% vs 6.5%
