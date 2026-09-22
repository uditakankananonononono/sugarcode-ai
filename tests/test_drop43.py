"""Drop 43: panel-wide conflicting-classification splice sweep. 977 ClinVar
splice variants where submitters DISAGREE on pathogenicity, across the 28
golden genes, scored on the real junction maps (same unfiltered machinery
as drop 42; "conflicting" is its own bucket here - drop 41 keeps it inside
pathogenic by description text and labels via clinvar_sig). 106 carry a
strong loss call - on record as ONE computational opinion, never a
tiebreaker; the fixture source says so.
"""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/conflicting_splice_golden.json").read_text())


def test_fixture_shape():
    assert len(FIX["genes"]) == 28
    assert sum(len(g["cases"]) for g in FIX["genes"].values()) == 977
    assert all(g["unmappable"] == 0 for g in FIX["genes"].values())


def test_strong_loss_counts():
    strong = [c for g in FIX["genes"].values() for c in g["cases"]
              if c["delta"] <= -0.15]
    assert len(strong) == 106


def test_honest_labeling():
    assert "not a tiebreaker" in FIX["source"]


def test_drop41_conflicting_gc_cases_present():
    # the 2 conflicting GC-donor cases from drop 41 appear here too
    here = {(g.upper(), c["notation"]) for g, d in FIX["genes"].items()
            for c in d["cases"]}
    assert ("BRCA2", "c.7976+4A>G") in here
    assert ("PALB2", "c.3350+2C>T") in here
