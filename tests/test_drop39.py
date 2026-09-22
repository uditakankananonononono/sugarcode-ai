"""Drop 39: GC-AG donor golden. 7 real ClinVar pathogenic variants at 3
real GC-AG donors (BRCA2 c.7976 incl. expert-panel +1G>A, ATM c.7515,
PALB2 c.3350) are ALL called loss (-0.254) on the documented GC
approximation matrix. Honest scope: the matrix is the GT matrix with the
+2 column swapped (7 observed GC donors too few for an independent
matrix); this golden validates the approximation on real pathogenic
evidence but cannot calibrate sensitivity (no benign GC-donor cases
exist in ClinVar at these donors)."""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/gc_donor_golden.json").read_text())


def test_fixture_shape():
    assert len(FIX["cases"]) == 7
    assert {c["gene"] for c in FIX["cases"]} == {"BRCA2", "ATM", "PALB2"}
    assert all(c["sig"] == "pathogenic" for c in FIX["cases"])


def test_all_gc_cases_called_loss():
    for c in FIX["cases"]:
        assert c["delta"] <= -0.15, c
        assert c["site_class"] == "GC"
        assert c["window"][3:5] == "GC"


def test_expert_panel_case_present():
    ep = [c for c in FIX["cases"] if "expert panel" in c["review"]]
    assert len(ep) == 1 and ep[0]["gene"] == "BRCA2" and ep[0]["notation"] == "c.7976+1G>A"
