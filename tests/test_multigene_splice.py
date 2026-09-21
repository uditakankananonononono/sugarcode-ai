"""Drop 24: multi-gene splice goldens - calibration is not BRCA1-specific.

Fixtures: ClinVar live pulls (2026-09-21/22) mapped onto title-verified
RefSeqGene records. Pooled: 610 pathogenic, 519 canonical +/-1/+/-2.
"""
import json
import re
from pathlib import Path

import pytest

GENES = ["brca1", "brca2", "mlh1", "cftr"]
FIX = {g: json.loads(Path(f"tests/fixtures/{g}_splice_golden.json").read_text())
       for g in GENES}


def _k(case):
    return int(re.search(r"[+-](\d+)", case["notation"]).group(1))


@pytest.mark.parametrize("gene,min_path,min_canonical_loss_frac", [
    ("brca1", 150, 1.00), ("brca2", 150, 0.98), ("mlh1", 100, 1.00), ("cftr", 100, 1.00),
])
def test_canonical_sites_called_loss_per_gene(gene, min_path, min_canonical_loss_frac):
    path = FIX[gene]["pathogenic"]
    assert len(path) >= min_path
    canon = [c for c in path if _k(c) <= 2]
    loss = sum(1 for c in canon if c["delta"] <= -0.15)
    assert loss / len(canon) >= min_canonical_loss_frac


def test_pooled_golden_size_and_calibration():
    path = [c for g in GENES for c in FIX[g]["pathogenic"]]
    ben = [c for g in GENES for c in FIX[g]["benign"]]
    assert len(path) == 610 and len(ben) == 32
    canon = [c for c in path if _k(c) <= 2]
    loss = sum(1 for c in canon if c["delta"] <= -0.15)
    assert loss / len(canon) >= 0.99
    tn = sum(1 for c in ben if c["delta"] > -0.15)
    assert tn / len(ben) >= 0.90


def test_gc_donor_misses_documented():
    """BRCA2 c.7976+2C>G / +2C>A destroy a GC-AG donor. GC donors (0.6% of
    junctions) were excluded from PWM training by design, so the model scores
    these ~0. Locked as the known scope limit, not tuned away."""
    miss = [c for c in FIX["brca2"]["pathogenic"]
            if c["notation"].startswith("c.7976+2C>")]
    assert len(miss) == 2
    assert all(abs(c["delta"]) < 0.05 for c in miss)
    assert all(c["window"][3:5] == "GC" for c in miss)


def test_benign_weakest_outlier_is_expert_panel():
    """BRCA2 c.9501+3A>T (ENIGMA-reviewed benign) is the strongest benign
    outlier at -0.108: +3 is conserved but this substitution is tolerated.
    Visible, not hidden."""
    c = next(c for c in FIX["brca2"]["benign"] if c["notation"] == "c.9501+3A>T")
    assert -0.15 < c["delta"] <= -0.10
    assert "expert panel" in c["review"]
