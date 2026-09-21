"""Multi-gene splice goldens - 7 genes, GC-aware (drops 24+25).

Fixtures: ClinVar live pulls (2026-09-21/22) mapped onto title-verified
RefSeqGene records. Pooled: 1,196 pathogenic + 44 benign; 1,042 canonical
+/-1/+/-2 sites, ALL called loss (100%); benign specificity 43/44 (98%).
"""
import json
import re
from pathlib import Path

import pytest

GENES = ["brca1", "brca2", "mlh1", "cftr", "msh2", "tp53", "nf1"]
FIX = {g: json.loads(Path(f"tests/fixtures/{g}_splice_golden.json").read_text())
       for g in GENES}
EXPECTED = {"brca1": (186, 20), "brca2": (170, 9), "mlh1": (128, 3), "cftr": (126, 0),
            "msh2": (92, 6), "tp53": (59, 4), "nf1": (435, 2)}


def _k(case):
    return int(re.search(r"[+-](\d+)", case["notation"]).group(1))


@pytest.mark.parametrize("gene", GENES)
def test_fixture_size_and_canonical_capture(gene):
    path, ben = FIX[gene]["pathogenic"], FIX[gene]["benign"]
    assert (len(path), len(ben)) == EXPECTED[gene]
    canon = [c for c in path if _k(c) <= 2]
    misses = [c["notation"] for c in canon if c["delta"] > -0.15]
    assert misses == [], f"{gene} canonical misses: {misses}"


def test_pooled_golden():
    path = [c for g in GENES for c in FIX[g]["pathogenic"]]
    ben = [c for g in GENES for c in FIX[g]["benign"]]
    assert (len(path), len(ben)) == (1196, 44)
    canon = [c for c in path if _k(c) <= 2]
    assert len(canon) == 1042
    assert all(c["delta"] <= -0.15 for c in canon)
    tn = sum(1 for c in ben if c["delta"] > -0.15)
    assert tn / len(ben) >= 0.95


def test_gc_donor_now_scored_with_gc_matrix():
    """BRCA2 c.7976+2C>G/A destroy a GC-AG donor. First golden (drop 24)
    missed them: GC donors are outside GT-matrix training. The swapped +2
    matrix (documented approximation) now calls both a loss; the variant
    carries the gc_donor flag and note instead of silently passing."""
    from sugarcode.modules.deepsplice import variant_at
    cases = [c for c in FIX["brca2"]["pathogenic"]
             if c["notation"].startswith("c.7976+2C>")]
    assert len(cases) == 2
    for c in cases:
        assert c["window"][3:5] == "GC" and c["delta"] <= -0.15
        r = variant_at(c["window"], c["index"], c["notation"][-1], "donor")
        assert r["gc_donor"] is True and "approximation" in r["gc_note"]


def test_gt_to_gc_conversion_scores_as_loss():
    """A +2T>C change at a GT donor must NOT be re-scored as a healthy GC
    donor (multi-gene golden caught this: ref-class matrix discipline).
    Every +2T>C pathogenic case in the pooled set must be a loss call."""
    conv = [c for g in GENES for c in FIX[g]["pathogenic"]
            if c["notation"].endswith("T>C") and _k(c) == 2 and "+" in c["notation"]]
    assert len(conv) >= 10
    assert all(c["delta"] <= -0.15 for c in conv)


def test_benign_outliers_visible():
    """The pooled benign false positive remains BRCA1 c.594-2A>C (ENIGMA
    benign at a conserved -2) - documented, not tuned away."""
    ben = [c for g in GENES for c in FIX[g]["benign"]]
    below = [c for c in ben if c["delta"] <= -0.15]
    assert [c["notation"] for c in below] == ["c.594-2A>C"]
