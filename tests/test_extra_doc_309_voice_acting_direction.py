import pytest
from sugarcode.extra_doc import voice_acting_direction as v

D = v.direct


def W(n):
    return " ".join(["w"] * n)


def L(words, sec, tgt=None):
    d = {"text": W(words), "seconds": sec}
    if tgt is not None:
        d["target_wpm"] = tgt
    return d


def test_constants():
    assert (v.MAX_LINES, v.TOLERANCE) == (500, 0.10)
    assert v.STATUS_NOTE.startswith("PARTIAL")


def test_hand_values_default_target_150():
    r = D([{"text": "one two three four five six", "seconds": 2.4}])
    x = r["lines"][0]
    assert x["words"] == 6 and x["wpm"] == pytest.approx(150.0) and x["ratio"] == pytest.approx(1.0)
    assert x["delivery"] == "on pace" and x["advice"] == "hold pace"
    assert r["status"] == v.STATUS_NOTE


def test_fast_and_slow():
    r = D([L(11, 4, 100), L(5, 6, 100), L(10, 6, 100)])  # 165 wpm, 50 wpm, 100 wpm
    a, b, c = r["lines"]
    assert (a["wpm"], a["ratio"], a["delivery"], a["advice"]) == (165.0, 1.65, "faster", "slow down")
    assert (b["wpm"], b["ratio"], b["delivery"], b["advice"]) == (50.0, 0.5, "slower", "speed up")
    assert (c["wpm"], c["delivery"], c["advice"]) == (100.0, "on pace", "hold pace")
    assert r["slow_down"] == 1 and r["speed_up"] == 1


def test_tolerance_edges_exact_10_percent_is_on_pace():
    assert D([L(11, 6, 100)])["lines"][0]["delivery"] == "on pace"   # 110 wpm, ratio 1.1
    assert D([L(9, 6, 100)])["lines"][0]["delivery"] == "on pace"    # 90 wpm, ratio 0.9
    assert D([L(111, 60, 100)])["lines"][0]["delivery"] == "faster"
    assert D([L(89, 60, 100)])["lines"][0]["delivery"] == "slower"


def test_word_count_splits_whitespace():
    assert D([{"text": "a  b\tc\n d", "seconds": 60, "target_wpm": 30}])["lines"][0]["words"] == 4
    assert D([{"text": "  solo ", "seconds": 60}])["lines"][0]["words"] == 1


def test_counts_over_many_lines():
    r = D([L(20, 6, 100)] * 3 + [L(1, 6, 100)] * 2 + [L(10, 6, 100)])
    assert r["slow_down"] == 3 and r["speed_up"] == 2 and len(r["lines"]) == 6


def test_target_and_seconds_edges():
    with pytest.raises(ValueError, match="seconds: must be within"):
        D([L(1, 0.0999)])
    assert D([L(1, 0.1, 30)])["lines"][0]["wpm"] == pytest.approx(600.0)
    assert D([L(1, 3600, 400)])["lines"][0]["wpm"] == pytest.approx(1 / 60)
    assert D([L(1, 3600, 30)])["lines"][0]["advice"] == "speed up"
    assert D([L(1, 60, 400)])["lines"][0]["ratio"] == pytest.approx(1 / 400)
    assert len(D([L(1, 1)] * 500)["lines"]) == 500


@pytest.mark.parametrize("bad", [
    [], [L(1, 1)] * 501, "ab", None, [5], [{"seconds": 1}], [{"text": 5, "seconds": 1}], [{"text": "", "seconds": 1}],
    [{"text": "   ", "seconds": 1}], [{"text": "a"}], [{"text": "a", "seconds": True}], [L(1, 0.09)], [L(1, 3600.5)],
    [L(1, float("nan"))], [L(1, "1")], [L(1, 1, 29)], [L(1, 1, 401)], [L(1, 1, True)], [L(1, 1, "150")],
    [L(1, 1, float("inf"))], [L(1, 2e9)], [L(1, 1, -2e9)],
])
def test_rejects(bad):
    with pytest.raises(ValueError):
        D(bad)


def test_messages():
    with pytest.raises(ValueError, match="lines: 1 to 500 required"):
        D([])
    with pytest.raises(ValueError, match="line: dict with text required"):
        D([5])
    with pytest.raises(ValueError, match="line: text has no words"):
        D([{"text": " ", "seconds": 1}])
    with pytest.raises(ValueError, match="seconds: number required"):
        D([{"text": "a"}])
    with pytest.raises(ValueError, match="seconds: must be within"):
        D([L(1, 0.05)])
    with pytest.raises(ValueError, match="target_wpm: must be within"):
        D([L(1, 1, 500)])
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        D([L(1, 1000000001.0)])
    with pytest.raises(ValueError, match="must be within"):
        D([L(1, 1e9)])
    with pytest.raises(ValueError, match="must be within"):
        D([L(1, 999999999)])
    with pytest.raises(ValueError, match="seconds: finite"):
        D([L(1, float("nan"))])


def test_independent_exact_oracle_random():
    import random
    from fractions import Fraction
    rnd = random.Random(3)
    for _ in range(150):
        n, sec, tgt = rnd.randint(1, 60), rnd.randint(1, 120), rnd.choice([60, 100, 120, 150, 200, 300])
        got = D([L(n, sec, tgt)])["lines"][0]
        ratio = Fraction(n * 60, sec) / tgt
        want = "faster" if ratio > Fraction(11, 10) else "slower" if ratio < Fraction(9, 10) else "on pace"
        assert got["delivery"] == want, (n, sec, tgt)
