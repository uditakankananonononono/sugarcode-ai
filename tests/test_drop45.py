"""Drop 45: exonic donor-window golden. ClinVar cites exonic splice-region
variants as CODING substitutions (c.NX>Y, no +/-), so the splice goldens
never harvested the donor's exonic -3..-1 positions. This sweep collected
every ClinVar variant cited at those positions across the 28 genes:
1,117 cases (334 pathogenic, 22 benign, 488 VUS, 194 conflicting, 79 other),
scored on the real junction maps. Findings: the donor PWM's exonic columns
already separate (terminal base: pathogenic mean -0.087 n=252 vs benign
-0.041 n=3; -2: -0.047 vs -0.010) - NO new model term needed; the value is
the evidence base. Honest limits: no case in any bucket crosses -0.15
(window-local PWMs under-score last-exonic-base pathogenic variants, the
known ESE/cryptic-mechanism gap); 'splice'[All Fields] misses coding
variants whose splice effect is recorded only as missense/nonsense.
"""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/exonic_donor_golden.json").read_text())
ALL = [c for g in FIX["genes"].values() for c in g["cases"]]


def test_fixture_shape():
    assert len(FIX["genes"]) == 28
    assert len(ALL) == 1117
    buckets = {}
    for c in ALL:
        buckets[c["sig"]] = buckets.get(c["sig"], 0) + 1
    assert buckets == {"vus": 488, "other": 79, "pathogenic": 334,
                       "conflicting": 194, "benign": 22}


def test_offsets_true():
    assert {c["exonic_offset"] for c in ALL} == {-1, -2, -3}
    import re
    for c in ALL:
        assert c["index"] == c["exonic_offset"] + 3
        refb = re.search(r"(\d)([ACGT])>", c["notation"]).group(2)
        assert c["window"][c["index"]] == refb


def test_terminal_base_separation():
    import statistics as st
    p = [c["delta"] for c in ALL if c["sig"] == "pathogenic" and c["exonic_offset"] == -1]
    b = [c["delta"] for c in ALL if c["sig"] == "benign" and c["exonic_offset"] == -1]
    assert len(p) == 252 and len(b) == 3
    assert st.mean(p) < st.mean(b)


def test_honest_weak_zone():
    assert not any(c["delta"] <= -0.15 for c in ALL)


def test_source_documents_scope():
    assert "coding substitutions" in FIX["source"]
    assert "-1 = terminal coding base" in FIX["source"]
