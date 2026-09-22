"""Drop 42: panel-wide VUS splice sweep fixture. 2,196 ClinVar VUS splice
variants across the 28 golden genes scored on the genes' real junction maps
(unfiltered query, germline-description bucketing - drop-41 discipline).
179 carry a strong loss call (delta <= -0.15): a prioritization signal for
reclassification work, NOT pathogenicity evidence - the fixture source note
says so. Zero cases unmappable. Per-gene extremes are real and kept: MYH7
carries 63 strong-loss VUS (42% of its 149), SCN1A/VHL/HBB/F8 carry zero.
"""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/vus_splice_golden.json").read_text())


def test_fixture_shape():
    assert len(FIX["genes"]) == 28
    tot = sum(len(g["cases"]) for g in FIX["genes"].values())
    assert tot == 2196
    assert all(g["unmappable"] == 0 for g in FIX["genes"].values())


def test_strong_loss_counts():
    strong = [c for g in FIX["genes"].values() for c in g["cases"]
              if c["delta"] <= -0.15]
    assert len(strong) == 179
    assert all(c["site_class"] in ("GT", "GC", "AG", "AT", "AC") for c in strong)


def test_honest_labeling():
    assert "NOT pathogenicity evidence" in FIX["source"]


def test_per_gene_extremes_kept():
    s = FIX["summary"]
    assert s["MYH7"]["strong_loss"] == 63
    assert s["SCN1A"]["strong_loss"] == 0
    assert s["MUTYH"]["vus"] == 0


def test_gc_vus_overlap_with_drop41():
    # the 10 GC-donor VUS from drop 41 also appear here (same underlying
    # variants, wider panel context) - no contradiction between fixtures
    gc_vus = {(c["gene"], c["notation"]) for c in
              json.loads(Path("tests/fixtures/gc_donor_golden.json")
                         .read_text())["cases"] if c["sig"] == "vus"}
    here = {(g.upper(), c["notation"]) for g, d in FIX["genes"].items()
            for c in d["cases"]}
    assert gc_vus <= here
