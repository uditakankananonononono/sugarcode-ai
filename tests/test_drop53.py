"""Drop 53: branch-point term wired as a NEW scoring surface (existing
paths untouched; both BP goldens re-scored through the public function)."""
import json
import pytest
from pathlib import Path

from sugarcode.modules.deepsplice import (branchpoint_score,
                                         branchpoint_variant_effect,
                                         BP_WEIGHT, BP_ZONE)

Z = json.loads(Path("tests/fixtures/branchzone_clinvar_golden.json").read_text())
L = json.loads(Path("tests/fixtures/branchpoint_variant_golden.json").read_text())


def _win(mer="CTCTAAT", pos=-25):
    w = list("T" * 60)
    i = 60 + pos - 5
    w[i:i + 7] = mer
    w[58:60] = "AG"
    return "".join(w)


def test_wired_scoring_mechanics():
    assert BP_ZONE == (-45, -18)
    assert BP_WEIGHT == 0.25
    assert branchpoint_score(_win()) > 5.0           # consensus candidate
    r = branchpoint_variant_effect(_win(), 60 - 25, "C")  # branch A>C
    assert r["bp_applicable"] and r["bp_drop_bits"] > 2.0
    assert r["delta"] == round(-BP_WEIGHT * r["bp_drop_bits"], 4)
    with pytest.raises(ValueError):
        branchpoint_score("ACGT")                     # wrong window length


def test_both_goldens_carry_wired_deltas():
    zc = [c for g in Z["genes"].values() for c in g["cases"]]
    assert len(zc) == 1923 and all("wired_delta" in c for c in zc)
    assert len(L["cases"]) == 73 and all("wired_delta" in c for c in L["cases"])
    for c in zc + L["cases"]:
        assert c["wired_delta"] == round(-BP_WEIGHT * c["bp_pwm_drop"], 4)


def test_wired_validation_numbers():
    bpz = [c for g in Z["genes"].values() for c in g["cases"] if c["in_bp_zone"]]
    p = [c["wired_delta"] for c in bpz if c["sig"] == "pathogenic"]
    b = [c["wired_delta"] for c in bpz if c["sig"] == "benign"]
    assert sum(d <= -0.15 for d in p) == 7    # 7/19 strong band
    assert sum(d <= -0.15 for d in b) == 1    # 1/31 -> ~97% specificity
