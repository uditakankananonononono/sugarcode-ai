from fractions import Fraction as Fr
import inspect
import pytest
from sugarcode.extra_doc import compensation_design as c

P = c.pay_grades


def test_constants():
    assert (c.MAX_MIDPOINT, c.MAX_GRADES, c.MAX_PROGRESSION_BPS, c.MAX_SPREAD_BPS, c.MAX_SALARIES, c.MAX_AMOUNT) == \
        (10**9, 30, 10000, 20000, 200, 10**10)
    assert c.STATUS_NOTE.startswith("PARTIAL") and "no judgment of what pay is right" in c.STATUS_NOTE
    assert inspect.signature(P).parameters["salaries"].default == ()


def test_hand_literals():
    # mid 1000, spread 50% (s = 1/2): min = 2000 / (5/2) = 800, max = 800 * 3/2 = 1200
    r = P(1000, 3, 2000, 5000)
    g1, g2, g3 = r["grades"]
    assert (g1["min"], g1["mid"], g1["max"]) == (800, 1000, 1200)
    assert (g2["min"], g2["mid"], g2["max"]) == (960, 1200, 1440)           # mid * 6/5 (20% progression)
    assert (g3["min"], g3["mid"], g3["max"]) == (Fr(5760, 5), Fr(1440), Fr(1728))
    assert g1["overlap"] == Fr(1200 - 960, 400) == Fr(3, 5)
    assert g2["overlap"] == Fr(1440 - 1152, 480) == Fr(3, 5)
    assert g3["overlap"] is None
    assert [x["grade"] for x in r["grades"]] == [1, 2, 3]
    r = P(1000, 2, 0, 5000, [(1, 1000), (1, 800), (1, 1200), (1, 799), (1, 1201), (2, 0)])
    assert [x["zone"] for x in r["salaries"]] == ["within", "within", "within", "below_min", "above_max", "below_min"]
    assert r["salaries"][0]["compa_ratio"] == 1 and r["salaries"][0]["range_position"] == Fr(1, 2)
    assert r["salaries"][1]["range_position"] == 0 and r["salaries"][2]["range_position"] == 1
    assert r["salaries"][3]["range_position"] == Fr(-1, 400) and r["salaries"][4]["range_position"] == Fr(401, 400)
    assert r["salaries"][5]["compa_ratio"] == 0
    assert P(1000, 2, 0, 5000)["grades"][0]["overlap"] == 1          # identical ranges overlap fully
    assert P(1000, 2, 10000, 100)["grades"][0]["overlap"] == 0       # doubling with a 1% spread: no overlap
    assert P(1000, 1, 0, 5000, [])["salaries"] == []


def test_oracle_random():
    import random
    rnd = random.Random(496)
    for _ in range(300):
        m, n = rnd.randint(1, 10**9), rnd.randint(1, 12)
        pb, sb = rnd.randint(0, 10000), rnd.randint(1, 20000)
        sal = [(rnd.randint(1, n), rnd.randint(0, 2 * 10**9)) for _ in range(rnd.randint(0, 5))]
        r = P(m, n, pb, sb, sal)
        mids = [Fr(m) * Fr(10000 + pb, 10000) ** i for i in range(n)]
        for i, row in enumerate(r["grades"]):
            lo = mids[i] * 2 / (2 + Fr(sb, 10000))
            hi = 2 * mids[i] - lo                      # the midpoint is halfway between min and max
            assert (row["min"], row["mid"], row["max"]) == (lo, mids[i], hi)
            assert (row["max"] - row["min"]) / row["min"] == Fr(sb, 10000)
            if i + 1 < n:
                lo2 = mids[i + 1] * 2 / (2 + Fr(sb, 10000))
                ov = (hi - lo2) / (hi - lo)
                assert row["overlap"] == (ov if ov > 0 else 0)
        for (g, a), out in zip(sal, r["salaries"]):
            row = r["grades"][g - 1]
            assert out["grade"] == g and out["amount"] == a
            assert out["compa_ratio"] == Fr(a) / mids[g - 1]
            assert out["range_position"] == (a - row["min"]) / (row["max"] - row["min"])
            assert out["zone"] == ("below_min" if a < row["min"] else "above_max" if a > row["max"] else "within")


def test_scalar_slots():
    for i, nm, lo, hi in ((0, "first_midpoint", 1, 10**9), (1, "grade_count", 1, 30),
                          (2, "progression_bps", 0, 10000), (3, "spread_bps", 1, 20000)):
        base = [1000, 3, 100, 100]
        for bad in (True, 1.0, "1", None):
            a = list(base); a[i] = bad
            with pytest.raises(ValueError, match=rf"{nm}: integer required"):
                P(*a)
        for bad in (lo - 1, hi + 1):
            a = list(base); a[i] = bad
            with pytest.raises(ValueError, match=rf"{nm}: must be within {lo} to {hi}"):
                P(*a)
        for good in (lo, hi):
            a = list(base); a[i] = good
            assert len(P(*a)["grades"]) == a[1]


def test_salary_slots():
    for bad in ("ab", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"salaries: list required"):
            P(1000, 3, 0, 100, bad)
    rows = [(1, 5)] * 201
    with pytest.raises(ValueError, match=r"salaries: at most 200 entries allowed"):
        P(1000, 3, 0, 100, rows)
    assert len(P(1000, 3, 0, 100, rows[:200])["salaries"]) == 200
    ok = (1, 5)
    for bad in ("ab", None, 5, {"a": 1}):
        with pytest.raises(ValueError, match=r"salaries\[1\]: \(grade, amount\) required"):
            P(1000, 3, 0, 100, [ok, bad])
    for bad in ((1,), (1, 2, 3), ()):
        with pytest.raises(ValueError, match=r"salaries\[1\]: 2 entries required"):
            P(1000, 3, 0, 100, [ok, bad])
    for i, nm, lo, hi in ((0, "grade", 1, 3), (1, "amount", 0, 10**10)):
        for bad in (True, 1.0, "1", None):
            e = [1, 5]; e[i] = bad
            with pytest.raises(ValueError, match=rf"salaries\[1\] {nm}: integer required"):
                P(1000, 3, 0, 100, [ok, tuple(e)])
        for bad in (lo - 1, hi + 1):
            e = [1, 5]; e[i] = bad
            with pytest.raises(ValueError, match=rf"salaries\[1\] {nm}: must be within {lo} to {hi}"):
                P(1000, 3, 0, 100, [ok, tuple(e)])
        for good in (lo, hi):
            e = [1, 5]; e[i] = good
            P(1000, 3, 0, 100, [ok, tuple(e)])
    assert P(1000, 3, 0, 100, [[2, 5]])["salaries"][0]["grade"] == 2
    assert P(1000, 5, 0, 100, [(5, 1)])["salaries"][0]["grade"] == 5          # grade bound follows grade_count
    with pytest.raises(ValueError, match=r"salaries\[0\] grade: must be within 1 to 2"):
        P(1000, 2, 0, 100, [(3, 1)])
