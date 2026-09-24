"""Rule Set 2 (Azimuth V3) port: fidelity tests against Microsoft's fixture.

tests/fixtures/azimuth_1000guides.csv is azimuth/tests/1000guides.csv from
https://github.com/MicrosoftResearch/Azimuth (BSD-3-Clause): 947 synthetic
30mers with reference scores produced by the original saved models in Nov
2016 ('truth pos' = V3_model_full, 'truth nopos' = V3_model_nopos). The
original library's own regression test asserts allclose at atol=1e-3.
"""
import os

import numpy as np
import pytest

from sugarcode.modules.crispr_opt.rule_set_2 import (
    featurize,
    score_guide,
    score_guides,
    tm_staluc,
)

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "azimuth_1000guides.csv")


def _fixture():
    import csv

    rows = []
    with open(FIXTURE) as fh:
        for rec in csv.DictReader(fh):
            rows.append(rec)
    return rows


ROWS = _fixture()
GUIDES = [r["guide"] for r in ROWS]
PP = [float(r["Percent peptide"]) for r in ROWS]
AA = [float(r["AA cut"]) for r in ROWS]
TRUTH_POS = np.array([float(r["truth pos"]) for r in ROWS])
TRUTH_NOPOS = np.array([float(r["truth nopos"]) for r in ROWS])


def test_full_model_reproduces_microsoft_reference_scores():
    pred = score_guides(GUIDES, PP, AA)
    assert np.allclose(pred, TRUTH_POS, atol=1e-3)
    # stronger than Microsoft's own tolerance: the port is exact to ~5e-10
    assert np.abs(pred - TRUTH_POS).max() < 1e-6


def test_nopos_model_reproduces_microsoft_reference_scores():
    pred = score_guides(GUIDES)
    assert np.allclose(pred, TRUTH_NOPOS, atol=1e-3)
    assert np.abs(pred - TRUTH_NOPOS).max() < 1e-6


def test_single_guide_matches_batch():
    batch = score_guides(GUIDES[:5], PP[:5], AA[:5])
    for i in range(5):
        assert score_guide(GUIDES[i], PP[i], AA[i]) == pytest.approx(batch[i], abs=1e-12)


def test_tm_staluc_matches_biopython_reference_values():
    # computed with Biopython 1.79 Bio.SeqUtils.MeltingTemp.Tm_staluc
    # (identical output to 1.66, the 2016-era release)
    assert tm_staluc("CAGAAAAAAAAACACTGCAACAAGAGGGTA") == pytest.approx(57.383334, abs=1e-5)
    assert tm_staluc("CAGTCAGTACGTACGTGTACTGCCGTA") == pytest.approx(59.865613, abs=1e-5)
    assert tm_staluc("AAAAA") == pytest.approx(-50.319302, abs=1e-5)
    assert tm_staluc("TTTTT") == pytest.approx(-50.319302, abs=1e-5)
    assert tm_staluc("GCGCGC") == pytest.approx(15.063024, abs=1e-5)


def test_featurize_dimensions_and_validation():
    assert featurize(GUIDES[0], PP[0], AA[0]).shape == (630,)
    assert featurize(GUIDES[0]).shape == (627,)
    with pytest.raises(ValueError):
        featurize("ACGT")  # not a 30mer
    with pytest.raises(ValueError):
        featurize("A" * 25 + "TTTTT")  # no NGG PAM


def test_scores_are_reasonable_rankings():
    # high-GC guides with poly-T context should not all collapse to one value
    pred = score_guides(GUIDES[:50])
    assert pred.std() > 0.01
    assert pred.min() > -0.5 and pred.max() < 1.5
