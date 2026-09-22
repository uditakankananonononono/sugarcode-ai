"""Drop 41: candidate (b) - benign specificity thickening at GC-AG
donors. Verdict, honestly: NO benign cases exist. ClinVar splice-window
variants at all three harvest GC donors (BRCA2 c.7976, ATM c.7515,
PALB2 c.3350) are pathogenic/likely (20), VUS (10), or conflicting (2,
bucketed with pathogenic by description text) - zero benign/likely-benign
after a full gene-level unfiltered sweep (drop-31 lesson applied: bucket
on germline description, not clinsig [Properties]). The specificity side
of the GC approximation matrix cannot be validated from ClinVar and the
fixture source note says so. What the thickening DID prove:
- 20/20 pathogenic cases called loss (delta < 0); +1/+2 all total loss.
- The earlier filtered query undercounted pathogenic cases 11 -> 20 by
  dropping Likely-only submissions - a real harvest-pipeline catch.
"""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/gc_donor_golden.json").read_text())


def test_no_benign_cases_documented():
    assert "benign" in FIX["source"].lower()
    assert not any(c["sig"] == "benign" for c in FIX["cases"])


def test_all_pathogenic_called_loss():
    path = [c for c in FIX["cases"] if c["sig"] == "pathogenic"]
    assert len(path) == 20
    assert all(c["delta"] < 0 for c in path)


def test_vus_cases_carried_not_dropped():
    vus = [c for c in FIX["cases"] if c["sig"] == "vus"]
    assert len(vus) == 10
    # VUS deltas span the weak zone - carried for future calibration,
    # never silently excluded from the fixture
    assert all(isinstance(c["delta"], float) for c in vus)


def test_conflicting_cases_labeled():
    confl = [c for c in FIX["cases"]
             if c["clinvar_sig"].startswith("Conflicting")]
    assert {c["notation"] for c in confl} == {"c.7976+4A>G", "c.3350+2C>T"}
