import itertools
import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc import visual_storyboarding as v

S = v.analyze_storyboard
SH = ["extreme_wide", "wide", "medium", "close", "extreme_close"]


def P(*items):
    return [{"id": f"p{i}", "shot": sh, "seconds": sec} for i, (sh, sec) in enumerate(items)]


def test_constants():
    assert v.SHOT_SCALE == {"extreme_wide": 1, "wide": 2, "medium": 3, "close": 4, "extreme_close": 5}
    assert (v.MAX_PANELS, v.MAX_ID, v.MAX_SECONDS, v.DEFAULT_JUMP, v.DEFAULT_RUN) == (300, 40, 600, 3, 3)
    assert v.STATUS_NOTE.startswith("PARTIAL")


def test_hand_literal():
    r = S(P(("wide", 2), ("wide", 1.5), ("wide", 3), ("extreme_close", 4), ("medium", 0.5), ("extreme_wide", 1)))
    assert [(x["start"], x["end"]) for x in r["panels"]] == [(0.0, 2.0), (2.0, 3.5), (3.5, 6.5), (6.5, 10.5), (10.5, 11.0), (11.0, 12.0)]
    assert [x["scale"] for x in r["panels"]] == [2, 2, 2, 5, 3, 1]
    assert r["total_seconds"] == 12.0 and r["mean_seconds"] == 2.0
    assert r["jump_cuts"] == [{"from": "p2", "to": "p3", "change": 3}]      # |5-2|=3 yes ; |3-5|=2 no ; |1-3|=2 no
    assert r["repeated_runs"] == [{"shot": "wide", "start_id": "p0", "length": 3}]
    assert r["shot_counts"] == {"wide": 3, "extreme_close": 1, "medium": 1, "extreme_wide": 1}


def test_thresholds_change_results():
    seq = P(("extreme_wide", 1), ("medium", 1), ("medium", 1), ("extreme_wide", 1))
    assert S(seq)["jump_cuts"] == [] and S(seq)["repeated_runs"] == []
    assert [j["change"] for j in S(seq, 2)["jump_cuts"]] == [2, -2]
    assert S(seq, 2, 2)["repeated_runs"] == [{"shot": "medium", "start_id": "p1", "length": 2}]
    assert S(seq, 3, 3) == S(seq)
    assert S(P(("extreme_wide", 1), ("extreme_close", 1)), 5)["jump_cuts"] == []   # change 4 < 5
    assert S(P(("extreme_wide", 1), ("extreme_close", 1)), 4)["jump_cuts"][0]["change"] == 4


def test_random_matches_groupby_oracle():
    rng = random.Random(280)
    for _ in range(60):
        n = rng.randint(1, 12)
        shots = [rng.choice(SH[:3]) if rng.random() < .7 else rng.choice(SH) for _ in range(n)]
        secs = [rng.choice([Fraction(1, 2), 1, 2, 3]) for _ in range(n)]
        rt = rng.randint(2, 5)
        r = S(P(*zip(shots, secs)), 2, rt)
        want_runs = []
        pos = 0
        for sh, grp in itertools.groupby(shots):
            ln = len(list(grp))
            if ln >= rt:
                want_runs.append({"shot": sh, "start_id": f"p{pos}", "length": ln})
            pos += ln
        assert r["repeated_runs"] == want_runs
        want_j = [(f"p{i}", f"p{i+1}") for i in range(n - 1) if abs(SH.index(shots[i]) - SH.index(shots[i + 1])) >= 2]
        assert [(j["from"], j["to"]) for j in r["jump_cuts"]] == want_j
        assert r["total_seconds"] == float(sum(secs))
        assert r["panels"][-1]["end"] == r["total_seconds"]


def test_validation():
    for bad, m in [([], "1..300"), ("x", "1..300"), ([5], r"panels\[0\]: dict"),
                   ([{"id": "", "shot": "wide", "seconds": 1}], "id must"),
                   ([{"id": "a" * 41, "shot": "wide", "seconds": 1}], "id must"),
                   ([{"id": "a", "shot": "huge", "seconds": 1}], "shot must be one of"),
                   ([{"id": "a", "shot": 3, "seconds": 1}], "shot must be one of"),
                   ([{"id": "a", "shot": "wide", "seconds": True}], "number required"),
                   ([{"id": "a", "shot": "wide", "seconds": "1"}], "number required"),
                   ([{"id": "a", "shot": "wide", "seconds": 0}], "above 0 and at most 600"),
                   ([{"id": "a", "shot": "wide", "seconds": -1}], "above 0 and at most 600"),
                   ([{"id": "a", "shot": "wide", "seconds": 600.5}], "above 0 and at most 600"),
                   ([{"id": "a", "shot": "wide", "seconds": float("nan")}], "finite"),
                   ([{"id": "a", "shot": "wide", "seconds": 1e10}], "magnitude above 1e9"),
                   ([{"id": "a", "shot": "wide", "seconds": 1}, {"id": "a", "shot": "wide", "seconds": 1}], "duplicate id")]:
        with pytest.raises(ValueError, match=m):
            S(bad)
    assert S([{"id": "a" * 40, "shot": "wide", "seconds": 600}])["total_seconds"] == 600.0
    assert S([{"id": "a", "shot": "wide", "seconds": Fraction(1, 1000)}])["total_seconds"] == 0.001
    for bad in [True, 1, 6, 2.0, "3"]:
        with pytest.raises(ValueError, match="jump_threshold: int in"):
            S(P(("wide", 1)), bad)
        with pytest.raises(ValueError, match="run_threshold: int in"):
            S(P(("wide", 1)), 3, bad)
    many = [{"id": f"p{i}", "shot": "wide", "seconds": 1} for i in range(301)]
    with pytest.raises(ValueError, match="1..300"):
        S(many)
    assert len(S(many[:300])["panels"]) == 300
    assert S(P(("wide", 1)), 5, 5)["total_seconds"] == 1.0
    assert S(P(("wide", 1)), 2, 2)["total_seconds"] == 1.0


def test_run_at_end_and_whole_sequence():
    r = S(P(("close", 1), ("wide", 1), ("wide", 1), ("wide", 1), ("wide", 1)))
    assert r["repeated_runs"] == [{"shot": "wide", "start_id": "p1", "length": 4}]
    assert S(P(("wide", 1), ("wide", 1)))["repeated_runs"] == []
    assert S(P(("wide", 1)) * 1)["mean_seconds"] == 1.0


def test_magnitude_cap_boundary():
    with pytest.raises(ValueError, match="above 0 and at most 600"):
        S([{"id": "a", "shot": "wide", "seconds": 1e9}])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        S([{"id": "a", "shot": "wide", "seconds": 1e9 + 1000}])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        S([{"id": "a", "shot": "wide", "seconds": -2e9}])
