import math
import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc import facial_animation as f

M = f.match_expression


def test_constants():
    assert f.PROTOTYPES == {"happiness": (6, 12), "sadness": (1, 4, 15), "surprise": (1, 2, 5, 26), "anger": (4, 5, 7, 23),
                            "fear": (1, 2, 4, 5, 20, 26), "disgust": (9, 15, 16)}
    assert f.KNOWN_AUS == (1, 2, 4, 5, 6, 7, 9, 12, 15, 16, 20, 23, 26)
    assert (f.MAX_INTENSITY, f.MATCH_COS_SQ) == (5, Fraction(9, 25)) and f.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal_smile():
    r = M({6: 3, 12: 3})
    assert r["label"] == "happiness"
    s = {x["emotion"]: x for x in r["scores"]}
    assert s["happiness"]["cosine"] == 1.0 and s["happiness"]["mean_intensity"] == 3.0
    assert [x["emotion"] for x in r["scores"]][0] == "happiness"
    assert all(x["cosine"] == 0.0 for k, x in s.items() if k != "happiness")


def test_hand_literal_partial_overlap():
    # x = {1:2, 2:2, 5:2, 26:2, 4:2}: surprise dot 8, |x|^2=20, |p|^2=4 -> cos^2 = 64/80 ; fear dot 10 -> 100/(20*6) ; sadness dot 4 -> 16/60
    r = M({1: 2, 2: 2, 5: 2, 26: 2, 4: 2})
    s = {x["emotion"]: x for x in r["scores"]}
    assert s["surprise"]["cosine"] == pytest.approx(math.sqrt(64 / 80)) and s["fear"]["cosine"] == pytest.approx(math.sqrt(100 / 120))
    assert s["sadness"]["cosine"] == pytest.approx(math.sqrt(16 / 60))
    assert r["label"] == "fear" and [x["emotion"] for x in r["scores"]][:2] == ["fear", "surprise"]   # 0.8333 beats 0.8
    assert s["surprise"]["mean_intensity"] == 2.0


def test_neutral_and_exact_threshold():
    assert M({6: 0, 12: 0})["label"] == "neutral_or_ambiguous"
    assert all(x["cosine"] == 0.0 for x in M({6: 0})["scores"])
    assert M({6: 3, 7: 4})["label"] == "neutral_or_ambiguous"      # happiness 9/(25*2)=0.18, anger 16/(25*4)=0.16
    assert M({6: 3, 12: 3, 9: 4})["label"] == "happiness"         # 36/(34*2) = 0.529
    # exactly cos^2 = 9/25: x = {6:3, 12:3, 9:4, 7:4}, |x|^2 = 50, happiness dot 6 -> 36/100
    r = M({6: 3, 12: 3, 9: 4, 7: 4})
    assert r["label"] == "happiness" and {x["emotion"]: x for x in r["scores"]}["happiness"]["cosine"] == pytest.approx(0.6)
    # a hair below: one extra unit of AU20 makes |x|^2 = 51 -> 36/102 < 0.36
    assert M({6: 3, 12: 3, 9: 4, 7: 4, 20: 1})["label"] == "neutral_or_ambiguous"


def test_tie_order_alphabetical():
    # AU 15 only: sadness (3 AUs) and disgust (3 AUs) tie at cos^2 1/3 -> alphabetical: disgust first
    r = M({15: 2})
    assert [x["emotion"] for x in r["scores"]][:2] == ["disgust", "sadness"]
    assert r["label"] == "neutral_or_ambiguous"            # 1/3 < 0.36


def test_random_cosine_oracle():
    rng = random.Random(297)
    for _ in range(80):
        x = {a: rng.randint(0, 5) for a in rng.sample(f.KNOWN_AUS, rng.randint(1, 8))}
        r = M(x)
        nx = math.sqrt(sum(v * v for v in x.values()))
        by = {s["emotion"]: s for s in r["scores"]}
        for name, proto in f.PROTOTYPES.items():
            vec = [1 if a in proto else 0 for a in f.KNOWN_AUS]
            xv = [x.get(a, 0) for a in f.KNOWN_AUS]
            want = 0.0 if nx == 0 else sum(p * q for p, q in zip(vec, xv)) / (nx * math.sqrt(sum(vec)))
            assert by[name]["cosine"] == pytest.approx(want, abs=1e-12)
            assert by[name]["mean_intensity"] == pytest.approx(sum(x.get(a, 0) for a in proto) / len(proto))
        cs = [s["cosine"] for s in r["scores"]]
        assert cs == sorted(cs, reverse=True)
        top = max(cs)
        assert (r["label"] == "neutral_or_ambiguous") == (top ** 2 < 0.36 - 1e-12)


def test_validation():
    for bad, m in [({}, "1..13"), ([6], "1..13"), ("x", "1..13"), ({3: 1}, "unknown action unit 3"), ({"6": 1}, "unknown action unit"),
                   ({True: 1}, "unknown action unit"), ({6: True}, "number required"), ({6: "2"}, "number required"),
                   ({6: float("nan")}, "finite"), ({6: -0.1}, r"must be within \[0, 5\]"), ({6: 5.1}, r"must be within \[0, 5\]")]:
        with pytest.raises(ValueError, match=m):
            M(bad)
    assert M({a: 5 for a in f.KNOWN_AUS})["scores"][0]["mean_intensity"] == 5.0
    assert M({6: 5})["scores"][0]["mean_intensity"] == 2.5
    assert M({6: Fraction(1, 3)})["scores"][0]["mean_intensity"] == pytest.approx(1 / 6)
    with pytest.raises(ValueError, match="1..13"):
        M({a: 1 for a in range(14)})
