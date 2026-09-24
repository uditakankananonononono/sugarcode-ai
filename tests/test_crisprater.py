"""Hermetic tests for the published CRISPRater model."""
import hashlib, json
from importlib.resources import files
import pytest
from sugarcode.modules.crisprater import score, score_many


def manual_score(s):
    values = [
        (s[3:13].count("G") + s[3:13].count("C")) / 10,  # published GC4-13 window (Labuhn 2018 Fig 4C)
        s[19] == "G", s[2] in "AT", s[11] in "AG", s[5] == "G",
        s[3] in "AT", s[17] in "AG", s[4] in "AC", s[13] == "G", s[14] == "A",
    ]
    weights = [.14177385, .06966514, .04216254, .03303432, .02355430,
               -.04746424, -.04878001, -.06981921, -.07087756, -.08160700]
    return .6505037 + sum(float(v) * w for v, w in zip(values, weights))


@pytest.mark.parametrize("spacer", [
    "ATCGATGCTGATGCTAGATA", "G" * 20, "A" * 20, "ACGT" * 5,
])
def test_exact_published_linear_formula(spacer):
    r = score(spacer)
    assert r.score == pytest.approx(manual_score(spacer))
    assert r.score == pytest.approx(r.intercept + sum(x.contribution for x in r.features))
    assert len(r.features) == 10


def test_primary_paper_class_boundaries(monkeypatch):
    import sugarcode.modules.crisprater.core as core
    base = {"features": [{"name": f"x{i}", "kind": "base", "position": 1,
                          "bases": "C", "coefficient": 0} for i in range(10)],
            "classes": {"low_max_exclusive": .56, "high_min_exclusive": .74}}
    for intercept, label in [(.5599, "low"), (.56, "medium"), (.74, "medium"), (.7401, "high")]:
        monkeypatch.setattr(core, "_model", lambda i=intercept: {**base, "intercept": i})
        assert core.score("A" * 20).efficacy_class == label


def test_batch_invariant_and_missing_explicit():
    a, b = "ATCGATGCTGATGCTAGATA", "G" * 20
    out = score_many([a, b, "N" * 20], errors="missing")
    assert out[0].score == score(a).score and out[1].score == score(b).score
    assert out[2] is None


@pytest.mark.parametrize("bad", ["A" * 19, "A" * 21, "A" * 19 + "N", ""])
def test_strict_validation(bad):
    with pytest.raises(ValueError): score(bad)


def test_vendored_model_integrity_and_shape():
    raw = files("sugarcode.modules.crisprater").joinpath("data/model.json").read_bytes()
    model = json.loads(raw)
    assert len(model["features"]) == 10
    assert hashlib.sha256(raw).hexdigest() == "5d0772c1d5a6dda2fa068957d5debd64a981aba7d7cd98c7c52dd6ceb73a9c11"  # corrected GC4-13 window
