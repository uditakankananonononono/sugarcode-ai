import inspect
import pytest
from sugarcode.extra_doc import key_management as k

A = k.audit


def test_constants():
    assert (k.MAX_KEYS, k.MAX_NAME, k.MAX_DAY, k.MAX_ROTATION, k.MAX_WARN) == (500, 60, 10**6, 3650, 3650)
    assert k.STATUSES == ("revoked", "overdue", "due_soon", "ok")
    assert k.STATUS_NOTE.startswith("PARTIAL") and "no key material handled" in k.STATUS_NOTE
    assert inspect.signature(A).parameters["warn_days"].default == 14


def test_hand_literals():
    ks = [("a", 0, 100, False), ("b", 50, 30, False), ("c", 90, 30, False), ("d", 10, 5, True), ("e", 100, 14, False)]
    r = A(ks, 100)
    assert [(x["age_days"], x["due_day"], x["days_left"], x["status"]) for x in r["keys"]] == [
        (100, 100, 0, "due_soon"), (50, 80, -20, "overdue"), (10, 120, 20, "ok"), (90, 15, -85, "revoked"),
        (0, 114, 14, "due_soon")]
    assert r["counts"] == {"revoked": 1, "overdue": 1, "due_soon": 2, "ok": 1}
    assert A([("a", 0, 10, False)], 9, 0)["keys"][0]["status"] == "ok"
    assert A([("a", 0, 10, False)], 10, 0)["keys"][0]["status"] == "due_soon"
    assert A([("a", 0, 10, False)], 11, 0)["keys"][0]["status"] == "overdue"
    assert A([("a", 0, 10, False)], 5, 5)["keys"][0]["status"] == "due_soon"
    assert A([("a", 0, 10, False)], 4, 5)["keys"][0]["status"] == "ok"
    assert A([("a", 5, 10, False)], 5)["keys"][0]["age_days"] == 0       # created today is allowed


def test_oracle_random():
    import random
    rnd = random.Random(528)
    for _ in range(500):
        today = rnd.randint(0, 5000)
        warn = rnd.randint(0, 60)
        ks = [(f"k{i}", rnd.randint(0, today), rnd.randint(1, 400), rnd.random() < .2) for i in range(rnd.randint(1, 10))]
        r = A(ks, today, warn)
        cnt = {"revoked": 0, "overdue": 0, "due_soon": 0, "ok": 0}
        for (n, c, rot, rev), o in zip(ks, r["keys"]):
            left = c + rot - today
            exp = "revoked" if rev else ("overdue" if left < 0 else ("due_soon" if left <= warn else "ok"))
            assert o == {"name": n, "age_days": today - c, "due_day": c + rot, "days_left": left, "status": exp}
            cnt[exp] += 1
        assert r["counts"] == cnt


def test_scalars_and_shape():
    ok = [("a", 0, 5, False)]
    for nm, lo, hi in (("today", 0, 10**6), ("warn_days", 0, 3650)):
        for bad in (True, 1.0, "1", None):
            kw = {"today": 10, "warn_days": 1}; kw[nm] = bad
            with pytest.raises(ValueError, match=rf"{nm}: integer required"):
                A(ok, **kw)
        for bad in (lo - 1, hi + 1):
            kw = {"today": 10, "warn_days": 1}; kw[nm] = bad
            with pytest.raises(ValueError, match=rf"{nm}: must be within {lo} to {hi}"):
                A(ok, **kw)
        for good in (lo, hi):
            kw = {"today": 10, "warn_days": 1}; kw[nm] = good
            A(ok, **kw)
    for bad in ("abc", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"keys: list required"):
            A(bad, 10)
    with pytest.raises(ValueError, match=r"keys: 1 to 500 entries required"):
        A([], 10)
    many = [(f"k{i}", 0, 5, False) for i in range(501)]
    with pytest.raises(ValueError, match=r"keys: 1 to 500 entries required"):
        A(many, 10)
    assert len(A(many[:500], 10)["keys"]) == 500
    for bad in ("abcd", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"keys\[1\]: \(name, created_day, rotation_days, revoked\) required"):
            A([ok[0], bad], 10)
    for bad in (("a", 0, 5), ("a", 0, 5, False, 1), ()):
        with pytest.raises(ValueError, match=r"keys\[1\]: 4 entries required"):
            A([ok[0], bad], 10)
    assert A([["a", 0, 5, False]], 10)["keys"][0]["status"] == "overdue"
    for bad in ("", "  ", None, 3, ["a"], "x" * 61):
        with pytest.raises(ValueError, match=r"keys\[1\] name: non-empty string up to 60 characters required"):
            A([ok[0], (bad, 0, 5, False)], 10)
    assert A([ok[0], ("x" * 60, 0, 5, False)], 10)["counts"]["overdue"] == 2
    for i, nm, lo, hi in ((1, "created_day", 0, 10**6), (2, "rotation_days", 1, 3650)):
        for bad in (True, 1.0, "1", None):
            row = ["b", 0, 5, False]; row[i] = bad
            with pytest.raises(ValueError, match=rf"keys\[1\] {nm}: integer required"):
                A([ok[0], tuple(row)], 10)
        for bad in (lo - 1, hi + 1):
            row = ["b", 0, 5, False]; row[i] = bad
            with pytest.raises(ValueError, match=rf"keys\[1\] {nm}: must be within {lo} to {hi}"):
                A([ok[0], tuple(row)], 10**6)
        for good in (lo, hi):
            row = ["b", 0, 5, False]; row[i] = good
            A([ok[0], tuple(row)], 10**6)
    with pytest.raises(ValueError, match=r"keys\[1\] created_day: must not be after today"):
        A([ok[0], ("b", 11, 5, False)], 10)
    for bad in (1, 0, None, "x"):
        with pytest.raises(ValueError, match=r"keys\[1\] revoked: bool required"):
            A([ok[0], ("b", 0, 5, bad)], 10)
    with pytest.raises(ValueError, match=r"keys\[2\]: duplicate key a"):
        A([ok[0], ("b", 0, 5, False), ("a", 0, 6, True)], 10)
