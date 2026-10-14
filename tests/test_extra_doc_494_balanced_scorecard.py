from fractions import Fraction as Fr
import pytest
from sugarcode.extra_doc import balanced_scorecard as b

S = b.scorecard
M = [("financial", "revenue", 90, 100, True), ("financial", "cost", 50, 40, False),
     ("customer", "nps", 30, 30, True), ("learning_growth", "training hrs", 20, 10, True),
     ("learning_growth", "turnover", 0, 5, False)]


def test_constants():
    assert b.PERSPECTIVES == ("financial", "customer", "internal_process", "learning_growth")
    assert (b.MAX_MEASURES, b.MAX_NAME, b.MAX_VALUE, b.MAX_WEIGHT, b.CAP) == (200, 60, 1_000_000_000, 100, 2)
    assert b.STATUS_NOTE.startswith("PARTIAL") and "no judgment of the" in b.STATUS_NOTE


def test_hand_literals():
    r = S(M)
    assert [m["attainment"] for m in r["measures"]] == [Fr(9, 10), Fr(4, 5), 1, 2, 2]
    assert r["scores"] == {"financial": Fr(17, 20), "customer": 1, "internal_process": None, "learning_growth": 2}
    assert r["status"] == {"financial": "amber", "customer": "green", "internal_process": None, "learning_growth": "green"}
    assert r["overall"] == (Fr(17, 20) + 1 + 2) / 3
    r = S(M, [1, 0, 5, 2])             # internal_process has no measures: its weight is excluded; customer weight 0
    assert r["overall"] == (1 * Fr(17, 20) + 2 * 2) / 3
    assert S(M, [0, 0, 5, 0])["overall"] is None
    assert S(M, [0, 0, 5, 1])["overall"] == 2
    r = S([("customer", "a", 3, 1, True)])                       # 3/1 capped at 2
    assert r["measures"][0]["attainment"] == 2
    r = S([("customer", "a", 2, 1, True)])
    assert r["measures"][0]["attainment"] == 2 and r["status"]["customer"] == "green"
    r = S([("customer", "a", 4, 5, True)])                       # exactly 4/5: amber
    assert r["status"]["customer"] == "amber" and r["scores"]["customer"] == Fr(4, 5)
    r = S([("customer", "a", 79, 100, True)])
    assert r["status"]["customer"] == "red"
    r = S([("customer", "a", 100, 100, True)])
    assert r["status"]["customer"] == "green"
    r = S([("customer", "a", 99, 100, True)])
    assert r["status"]["customer"] == "amber"
    r = S([("financial", "cost", 40, 100, False)])               # lower is better: 100/40 = 2.5 capped at 2
    assert r["measures"][0]["attainment"] == 2
    r = S([("financial", "cost", 200, 100, False)])
    assert r["measures"][0]["attainment"] == Fr(1, 2) and r["status"]["financial"] == "red"
    r = S([("financial", "cost", 1, 1_000_000_000, False), ("financial", "cost", 1, 1, False)][:1])
    assert r["measures"][0]["attainment"] == 2
    assert S([("financial", "x", 0, 7, True)])["scores"]["financial"] == 0
    assert S([("financial", "x", 5, 5, True), ("customer", "x", 5, 5, True)])["measures"][1]["name"] == "x"


def ok(**kw):
    return [("customer", "a", 1, 1, True)]


def test_weights_slots():
    with pytest.raises(ValueError, match=r"weights: list required"):
        S(ok(), "1111")
    with pytest.raises(ValueError, match=r"weights: list required"):
        S(ok(), None)
    for bad in ([1, 1, 1], [1, 1, 1, 1, 1], []):
        with pytest.raises(ValueError, match=r"weights: 4 entries required"):
            S(ok(), bad)
    for i in range(4):
        for bad in (True, 1.0, "1", None):
            w = [1, 1, 1, 1]; w[i] = bad
            with pytest.raises(ValueError, match=rf"weights\[{i}\]: integer required"):
                S(ok(), w)
        for bad in (-1, 101):
            w = [1, 1, 1, 1]; w[i] = bad
            with pytest.raises(ValueError, match=rf"weights\[{i}\]: must be within 0 to 100"):
                S(ok(), w)
        for good in (0, 100):
            w = [1, 1, 1, 1]; w[i] = good
            assert S(ok(), tuple(w))["scores"]["customer"] == 1


def test_measures_shape():
    for bad in ("abc", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"measures: list required"):
            S(bad)
    with pytest.raises(ValueError, match=r"measures: 1 to 200 entries required"):
        S([])
    row = [("customer", f"m{i}", 1, 1, True) for i in range(201)]
    with pytest.raises(ValueError, match=r"measures: 1 to 200 entries required"):
        S(row)
    assert len(S(row[:200])["measures"]) == 200 and len(S(row[:1])["measures"]) == 1
    for bad in ("custo", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"measures\[1\]: \(perspective, name, actual, target, higher_is_better\) required"):
            S([ok()[0], bad])
    for bad in (("customer", "a", 1, 1), ("customer", "a", 1, 1, True, 0), ()):
        with pytest.raises(ValueError, match=r"measures\[1\]: 5 entries required"):
            S([ok()[0], bad])
    assert S([["customer", "a", 1, 1, True]])["scores"]["customer"] == 1     # list row accepted


def test_measure_slots():
    base = ["customer", "a", 5, 10, True]

    def row(i, v):
        r = list(base); r[i] = v
        return [("financial", "z", 1, 1, True), tuple(r)]
    for bad in ("Customer", "", None, 3, ["customer"]):
        with pytest.raises(ValueError, match=r"measures\[1\] perspective: one of financial, customer, internal_process, learning_growth required"):
            S(row(0, bad))
    for bad in ("", "   ", None, 3, ["a"], "x" * 61):
        with pytest.raises(ValueError, match=r"measures\[1\] name: non-empty string up to 60 characters required"):
            S(row(1, bad))
    assert S(row(1, "x" * 60))["measures"][1]["name"] == "x" * 60
    for i, nm, lo, hi in ((2, "actual", 0, 10**9), (3, "target", 1, 10**9)):
        for bad in (True, 1.0, "1", None):
            with pytest.raises(ValueError, match=rf"measures\[1\] {nm}: integer required"):
                S(row(i, bad))
        for bad in (lo - 1, hi + 1):
            with pytest.raises(ValueError, match=rf"measures\[1\] {nm}: must be within {lo} to {hi}"):
                S(row(i, bad))
        for good in (lo, hi):
            S(row(i, good))
    for bad in (1, 0, None, "True"):
        with pytest.raises(ValueError, match=r"measures\[1\] higher_is_better: bool required"):
            S(row(4, bad))
    with pytest.raises(ValueError, match=r"measures\[2\]: duplicate measure a in customer"):
        S([("financial", "z", 1, 1, True), ("customer", "a", 1, 1, True), ("customer", "a", 2, 2, False)])
    assert len(S([("financial", "a", 1, 1, True), ("customer", "a", 1, 1, True)])["measures"]) == 2
    assert S([("customer", "a", 1, 1, True)], weights=[5, 5, 5, 5])["overall"] == 1
    import inspect
    assert inspect.signature(S).parameters["weights"].default == (1, 1, 1, 1)


def test_oracle_random():
    import random
    rnd = random.Random(494)
    P = b.PERSPECTIVES
    for _ in range(400):
        ms = []
        for k in range(rnd.randint(1, 8)):
            hib = rnd.random() < .5
            ms.append((rnd.choice(P), f"n{k}", rnd.choice([0, 1, 7, 50, 100, 10**9, rnd.randint(0, 200)]),
                       rnd.choice([1, 3, 100, 10**9, rnd.randint(1, 200)]), hib))
        w = [rnd.randint(0, 5) for _ in P]
        r = S(ms, w)
        att = []
        for _p, _n, a, t, h in ms:
            v = Fr(a, t) if h else (Fr(2) if a == 0 else Fr(t, a))
            att.append(min(v, Fr(2)))
        assert [m["attainment"] for m in r["measures"]] == att
        num = den = Fr(0)
        for j, p in enumerate(P):
            xs = [att[i] for i, m in enumerate(ms) if m[0] == p]
            if not xs:
                assert r["scores"][p] is None and r["status"][p] is None
                continue
            sc = sum(xs) / len(xs)
            assert r["scores"][p] == sc
            assert r["status"][p] == ("green" if sc >= 1 else "amber" if sc * 5 >= 4 else "red")
            num += w[j] * sc; den += w[j]
        assert r["overall"] == (num / den if den else None)
