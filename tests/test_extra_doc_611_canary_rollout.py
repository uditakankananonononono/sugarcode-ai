import inspect
import math
import random
from fractions import Fraction as F

import pytest
from sugarcode.extra_doc import canary_rollout as cr

P = cr.plan


def rows(r):
    return [(x["percent"], x["total"], x["new"], x["empty"]) for x in r["steps"]]


def test_constants_signature():
    assert (cr.MAX_INSTANCES, cr.MAX_STEPS) == (10000, 10)
    assert cr.STATUS_NOTE.startswith("PARTIAL") and "nothing is deployed" in cr.STATUS_NOTE
    assert list(inspect.signature(P).parameters) == ["instances", "steps"]


def test_hand_literals():
    r = P(50, [10, 50, 100])
    assert rows(r) == [(10, 5, 5, False), (50, 25, 20, False), (100, 50, 25, False)]
    assert r["status_note"] == cr.STATUS_NOTE
    assert rows(P(7, [10, 20, 100])) == [(10, 1, 1, False), (20, 2, 1, False), (100, 7, 5, False)]   # 0.7 -> 1, 1.4 -> 2
    assert rows(P(3, [1, 2, 100])) == [(1, 1, 1, False), (2, 1, 0, True), (100, 3, 2, False)]       # rounds up, empty step
    assert rows(P(1, [1, 100])) == [(1, 1, 1, False), (100, 1, 0, True)]
    assert rows(P(10000, [1, 100])) == [(1, 100, 100, False), (100, 10000, 9900, False)]
    assert rows(P(100, [100])) == [(100, 100, 100, False)]
    assert rows(P(101, [50, 100])) == [(50, 51, 51, False), (100, 101, 50, False)]                  # 50.5 -> 51
    assert rows(P(200, [25, 50, 75, 100])) == [(25, 50, 50, False), (50, 100, 50, False), (75, 150, 50, False), (100, 200, 50, False)]
    assert rows(P(4, (25, 100))) == [(25, 1, 1, False), (100, 4, 3, False)]


def test_oracle_fraction_ceil():
    rnd = random.Random(611)
    for _ in range(500):
        n = rnd.randint(1, 300)
        k = rnd.randint(1, 10)
        steps = sorted(rnd.sample(range(1, 100), k - 1)) + [100]
        r = P(n, steps)
        prev = 0
        for s, x in zip(steps, r["steps"]):
            want = math.ceil(F(n * s, 100))
            assert x["total"] == want and x["new"] == want - prev and x["empty"] == (want == prev)
            prev = want
        assert r["steps"][-1]["total"] == n and sum(x["new"] for x in r["steps"]) == n


def test_caps_both_sides():
    assert P(10000, [100])["steps"][0]["total"] == 10000
    with pytest.raises(ValueError, match=r"^instances: must be within 1 to 10000$"):
        P(10001, [100])
    with pytest.raises(ValueError, match=r"^instances: must be within 1 to 10000$"):
        P(0, [100])
    assert len(P(10, [10, 20, 30, 40, 50, 60, 70, 80, 90, 100])["steps"]) == 10
    with pytest.raises(ValueError, match=r"^steps: 1 to 10 entries required$"):
        P(10, [5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    with pytest.raises(ValueError, match=r"^steps: 1 to 10 entries required$"):
        P(10, [])
    assert P(10, [1, 100])["steps"][0]["percent"] == 1
    with pytest.raises(ValueError, match=r"^steps\[0\]: must be within 1 to 100$"):
        P(10, [0, 100])
    with pytest.raises(ValueError, match=r"^steps\[1\]: must be within 1 to 100$"):
        P(10, [50, 101])


def test_ordering_and_end_rules():
    with pytest.raises(ValueError, match=r"^steps\[1\]: must be greater than the previous step$"):
        P(10, [50, 50, 100])
    with pytest.raises(ValueError, match=r"^steps\[1\]: must be greater than the previous step$"):
        P(10, [60, 50, 100])
    with pytest.raises(ValueError, match=r"^steps: last step must be 100$"):
        P(10, [10, 99])
    with pytest.raises(ValueError, match=r"^steps: last step must be 100$"):
        P(10, [50])
    assert P(10, [99, 100])["steps"][0]["total"] == 10


def test_type_refusals_and_order():
    for bad in (True, False, 1.0, "1", None):
        with pytest.raises(ValueError, match=r"^instances: integer required$"):
            P(bad, [100])
        with pytest.raises(ValueError, match=r"^steps\[0\]: integer required$"):
            P(10, [bad, 100])
    for bad in ("ab", None, 5, {1: 1}):
        with pytest.raises(ValueError, match=r"^steps: list required$"):
            P(10, bad)
    with pytest.raises(ValueError, match=r"^instances: integer required$"):
        P(True, "bad")
    with pytest.raises(ValueError, match=r"^steps\[0\]: integer required$"):
        P(10, [True, 10**30])
    with pytest.raises(ValueError, match=r"^steps\[1\]: must be within 1 to 100$"):
        P(10, [50, 10**30])


def test_decrease_checked_against_previous_step_not_first():
    # a mutant comparing with the first step (pcts[0]) would accept these
    for inst, steps, idx in ((5, [10, 50, 40, 100], 2), (7, [20, 60, 30, 100], 2), (9, [5, 30, 90, 20, 100], 3),
                             (9, [1, 2, 80, 79, 100], 3), (3, [10, 11, 50, 49, 100], 3)):
        with pytest.raises(ValueError, match=rf"^steps\[{idx}\]: must be greater than the previous step$"):
            P(inst, steps)
