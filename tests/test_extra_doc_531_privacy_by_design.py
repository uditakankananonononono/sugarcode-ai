from fractions import Fraction as Fr
import pytest
from sugarcode.extra_doc import privacy_by_design as p

A = p.audit


def test_constants():
    assert (p.MAX_FIELDS, p.MAX_NAME, p.MAX_SENSITIVITY, p.MAX_DAY, p.MAX_RETENTION) == (200, 60, 3, 10**6, 36500)
    assert p.RETENTION_STATES == ("within", "due", "overdue")
    assert p.STATUS_NOTE.startswith("PARTIAL") and "no judgment of lawfulness" in p.STATUS_NOTE


def test_hand_literals():
    fs = [("email", True, 2, 0, 100), ("nickname", False, 1, 50, 100), ("location", False, 3, 90, 5),
          ("avatar", True, 0, 0, 30)]
    r = A(fs, 100)
    assert [(x["age_days"], x["days_over"], x["retention"]) for x in r["fields"]] == [
        (100, 0, "due"), (50, 0, "within"), (10, 5, "overdue"), (100, 70, "overdue")]
    assert r["unneeded"] == ["location", "nickname"]                 # worst sensitivity first
    assert r["overdue"] == ["location", "avatar"]                    # input order
    assert r["needed_share"] == Fr(1, 2) and r["unneeded_sensitivity"] == 4
    assert A([("a", False, 0, 0, 1)], 0)["unneeded_sensitivity"] == 0
    assert A([("a", True, 3, 5, 10)], 5)["fields"][0]["age_days"] == 0
    assert A([("a", True, 0, 0, 10)], 9)["fields"][0]["retention"] == "within"
    assert A([("a", True, 0, 0, 10)], 10)["fields"][0]["retention"] == "due"
    assert A([("a", True, 0, 0, 10)], 11)["fields"][0]["retention"] == "overdue"
    r = A([("a", False, 1, 0, 9), ("b", False, 1, 0, 9), ("c", False, 2, 0, 9)], 0)
    assert r["unneeded"] == ["c", "a", "b"]                          # ties keep input order
    assert A([("a", False, 1, 0, 9)], 10)["overdue"] == ["a"]


def test_oracle_random():
    import random
    rnd = random.Random(531)
    for _ in range(500):
        today = rnd.randint(0, 5000)
        fs = [(f"f{i}", rnd.random() < .7, rnd.randint(0, 3), rnd.randint(0, today), rnd.randint(1, 400))
              for i in range(rnd.randint(1, 12))]
        r = A(fs, today)
        rows = []
        for (n, need, s, c, ret), o in zip(fs, r["fields"]):
            age = today - c
            state = "overdue" if age > ret else ("due" if age == ret else "within")
            rows.append({"name": n, "needed": need, "sensitivity": s, "age_days": age,
                         "days_over": max(0, age - ret), "retention": state})
            assert o == rows[-1]
        exp_un = sorted(((f[2], i, f[0]) for i, f in enumerate(fs) if not f[1]), key=lambda x: (-x[0], x[1]))
        assert r["unneeded"] == [n for _, _, n in exp_un]
        assert r["overdue"] == [x["name"] for x in rows if x["retention"] == "overdue"]
        assert r["needed_share"] == Fr(sum(1 for f in fs if f[1]), len(fs))
        assert r["unneeded_sensitivity"] == sum(f[2] for f in fs if not f[1])


def test_validation():
    ok = ("a", True, 0, 0, 5)
    for nm, lo, hi in (("today", 0, 10**6),):
        for bad in (True, 1.0, "1", None, lo - 1, hi + 1):
            with pytest.raises(ValueError, match=rf"{nm}:"):
                A([ok], bad)
        for good in (lo, hi):
            A([ok], good)
    for bad in ("abc", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"fields: list required"):
            A(bad, 10)
    with pytest.raises(ValueError, match=r"fields: 1 to 200 entries required"):
        A([], 10)
    many = [(f"f{i}", True, 0, 0, 5) for i in range(201)]
    with pytest.raises(ValueError, match=r"fields: 1 to 200 entries required"):
        A(many, 10)
    assert len(A(many[:200], 10)["fields"]) == 200
    for bad in ("abcde", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"fields\[1\]: \(name, needed, sensitivity, collected_day, retention_days\) required"):
            A([ok, bad], 10)
    for bad in (("b", True, 0, 0), ("b", True, 0, 0, 5, 1), ()):
        with pytest.raises(ValueError, match=r"fields\[1\]: 5 entries required"):
            A([ok, bad], 10)
    for bad in ("", "  ", None, 3, ["b"], "x" * 61):
        with pytest.raises(ValueError, match=r"fields\[1\] name: non-empty string up to 60 characters required"):
            A([ok, (bad, True, 0, 0, 5)], 10)
    assert A([ok, ("x" * 60, True, 0, 0, 5)], 10)["fields"][1]["name"] == "x" * 60
    with pytest.raises(ValueError, match=r"fields\[2\]: duplicate field a"):
        A([ok, ("b", True, 0, 0, 5), ("a", False, 1, 0, 5)], 10)
    for bad in (1, 0, None, "x"):
        with pytest.raises(ValueError, match=r"fields\[1\] needed: bool required"):
            A([ok, ("b", bad, 0, 0, 5)], 10)
    for i, nm, lo, hi in ((2, "sensitivity", 0, 3), (3, "collected_day", 0, 10**6), (4, "retention_days", 1, 36500)):
        for bad in (True, 1.0, "1", None):
            row = ["b", True, 0, 0, 5]; row[i] = bad
            with pytest.raises(ValueError, match=rf"fields\[1\] {nm}: integer required"):
                A([ok, tuple(row)], 10)
        for bad in (lo - 1, hi + 1):
            row = ["b", True, 0, 0, 5]; row[i] = bad
            with pytest.raises(ValueError, match=rf"fields\[1\] {nm}: must be within {lo} to {hi}"):
                A([ok, tuple(row)], 10**6)
        for good in (lo, hi):
            row = ["b", True, 0, 0, 5]; row[i] = good
            A([ok, tuple(row)], 10**6)
    with pytest.raises(ValueError, match=r"fields\[1\] collected_day: must not be after today"):
        A([ok, ("b", True, 0, 11, 5)], 10)
    assert A([[ "a", True, 0, 0, 5]], 10)["fields"][0]["name"] == "a"   # list rows accepted
