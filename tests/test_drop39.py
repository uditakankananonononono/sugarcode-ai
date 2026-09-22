"""Drop 39: GC-AG donor golden. Real ClinVar variants at 3 real GC-AG
donors (BRCA2 c.7976 incl. expert-panel +1G>A, ATM c.7515, PALB2 c.3350).
Drop 41 thickened the fixture: full +/-1..+6 window, ALL classifications
via germline-description bucketing (the drop-31 lesson - clinsig
[Properties] filters silently drop Likely-only and VUS variants).
Honest scope: the matrix is the GT matrix with the +2 column swapped
(7 observed GC donors too few for an independent matrix); the golden
validates the approximation on real pathogenic evidence. ZERO benign
cases exist in ClinVar at these donors (searched 2026-09-22) - the
specificity side stays unprovable and says so."""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/gc_donor_golden.json").read_text())


def test_fixture_shape():
    assert len(FIX["cases"]) == 30
    assert {c["gene"] for c in FIX["cases"]} == {"BRCA2", "ATM", "PALB2"}
    buckets = {}
    for c in FIX["cases"]:
        buckets[c["sig"]] = buckets.get(c["sig"], 0) + 1
    assert buckets == {"pathogenic": 20, "vus": 10}
    assert "benign" not in buckets  # searched, found zero - documented


def test_core_gc_cases_called_loss():
    # every +1/+2 substitution is total loss on the GC matrix
    core = [c for c in FIX["cases"] if c["index"] <= 4]
    assert len(core) == 14
    for c in core:
        assert c["delta"] <= -0.15, c
        assert c["site_class"] == "GC"
        assert c["window"][3:5] == "GC"


def test_expert_panel_cases_present():
    ep = [c for c in FIX["cases"] if "expert panel" in c["review"]]
    assert {c["notation"] for c in ep} == {"c.7976+1G>A", "c.3350+4A>G"}


def test_weak_zone_is_weak():
    # +3..+6: window-local deltas are small; several are ClinVar-pathogenic
    # anyway (documented limit of window-local scoring)
    weak = [c for c in FIX["cases"] if c["index"] >= 5]
    assert weak and all(-0.15 < c["delta"] < 0 for c in weak)
