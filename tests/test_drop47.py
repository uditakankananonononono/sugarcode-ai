"""Drop 47: exonic acceptor-window sweep (mirror of drop 45). The acceptor
key c.N is the FIRST coding base of the incoming exon -> window index 14,
the only exonic position in the 15-mer acceptor window. 216 ClinVar coding
substitutions at those positions across the 28 genes (32 pathogenic, 2
benign, 122 VUS, 40 conflicting, 20 other), scored on the real maps.
Findings: direction is consistent (pathogenic mean -0.0246 vs benign
-0.0069) but benign n=2 - NO specificity statement is possible and none is
made; the single exonic acceptor column carries weak information. No case
crosses -0.15. No model change - evidence base only, like drop 45.
"""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/exonic_acceptor_golden.json").read_text())
ALL = [c for g in FIX["genes"].values() for c in g["cases"]]


def test_fixture_shape():
    assert len(FIX["genes"]) == 28
    assert len(ALL) == 216
    buckets = {}
    for c in ALL:
        buckets[c["sig"]] = buckets.get(c["sig"], 0) + 1
    assert buckets == {"conflicting": 40, "vus": 122, "pathogenic": 32,
                       "benign": 2, "other": 20}


def test_all_first_exonic_base():
    assert {c["exonic_offset"] for c in ALL} == {1}
    assert all(c["index"] == 14 and c["site_type"] == "acceptor" for c in ALL)
    import re
    for c in ALL:
        refb = re.search(r"(\d)([ACGT])>", c["notation"]).group(2)
        assert c["window"][14] == refb


def test_direction_consistent_but_thin():
    import statistics as st
    p = [c["delta"] for c in ALL if c["sig"] == "pathogenic"]
    b = [c["delta"] for c in ALL if c["sig"] == "benign"]
    assert st.mean(p) < st.mean(b)
    assert len(b) <= 2  # documented: too thin for a specificity claim


def test_no_strong_calls():
    assert not any(c["delta"] <= -0.15 for c in ALL)
