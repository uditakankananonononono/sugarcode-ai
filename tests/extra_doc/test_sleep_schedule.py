import copy
import datetime as dt
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import sleep_schedule as m
from sugarcode.extra_doc.sleep_schedule import SleepError, sleep_schedule as run

KEYS = "data keys must be exactly nights, target"
NI = "nights must be a list of 1..60 [bedtime, waketime] pairs"


def d(nights=((1380, 420), (1410, 450), (60, 480)), target=420):
    return {"nights": [list(n) for n in nights], "target": target}


def bad(data, msg):
    with pytest.raises(SleepError) as e:
        run(data)
    assert str(e.value) == msg


def check(x):
    """Independent: real datetimes. Wake is the first moment at that clock time strictly after bedtime;
    bedtime offsets are taken from the preceding noon."""
    o = run(x)
    base = dt.datetime(2026, 1, 10)
    durs, offs = [], []
    for b, w in x["nights"]:
        bed = base + dt.timedelta(minutes=b)
        wake = base + dt.timedelta(minutes=w)
        while wake <= bed:
            wake += dt.timedelta(days=1)
        durs.append(int((wake - bed) / dt.timedelta(minutes=1)))
        noon = base.replace(hour=12)
        if bed < noon:
            noon -= dt.timedelta(days=1)
        offs.append(int((bed - noon) / dt.timedelta(minutes=1)))
    assert o["durations"] == durs
    assert F(o["mean_duration"]) == F(sum(durs), len(durs))
    assert o["nights_at_target"] == sum(v >= x["target"] for v in durs)
    assert (o["shortest"], o["longest"]) == (min(durs), max(durs))
    assert o["bedtime_spread"] == max(offs) - min(offs)
    return o


def test_hand_worked():
    o = run(d())
    # 23:00->07:00 = 480 ; 23:30->07:30 = 480 ; 01:00->08:00 = 420
    assert o["durations"] == [480, 480, 420] and o["mean_duration"] == "460"
    assert o["nights_at_target"] == 3 and (o["shortest"], o["longest"]) == (420, 480)
    # offsets from noon: 660, 690, 780 -> spread 120
    assert o["bedtime_spread"] == 120
    assert o["status"] == "completed"
    assert o["claims"] == {"accurate_times": False, "target_valid": False, "regularity_healthy": False, "health_claim": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_edges():
    assert check(d([(0, 1)], 60))["durations"] == [1]
    assert check(d([(1, 0)], 60))["durations"] == [1439]
    assert check(d([(1439, 0)], 60))["durations"] == [1]
    assert check(d([(0, 1439)], 1440))["nights_at_target"] == 0
    assert check(d([(1, 0)], 1440))["nights_at_target"] == 0
    assert check(d([(720, 719)], 1440))["durations"] == [1439]
    assert check(d([(100, 100 + 59)], 60))["nights_at_target"] == 0
    assert check(d([(100, 160)], 60))["nights_at_target"] == 1
    assert check(d([(719, 5), (720, 5)]))["bedtime_spread"] == 1439   # 719 is just before noon so it is the latest
    assert check(d([(700, 5)]))["bedtime_spread"] == 0


def test_random():
    rng = random.Random(809)
    for _ in range(500):
        ns = []
        for _ in range(rng.randint(1, 8)):
            b = rng.randint(0, 1439)
            w = rng.choice([x for x in (rng.randint(0, 1439), (b + rng.randint(1, 600)) % 1440) if x != b] or [(b + 1) % 1440])
            ns.append((b, w))
        check(d(ns, rng.randint(60, 1440)))


def test_caps():
    run(d([(0, 1)] * 60))
    bad(d([(0, 1)] * 61), NI)
    bad(d([(0, 1)] * 10**5), NI)
    bad(d([]), NI)
    bad(d([(1440, 5)]), "bedtime out of range")
    bad(d([(-1, 5)]), "bedtime out of range")
    bad(d([(5, 1440)]), "waketime out of range")
    bad(d([(5, -1)]), "waketime out of range")
    bad(d([(5, 5)]), "bedtime and waketime must differ")
    bad(d(target=59), "target out of range")
    bad(d(target=1441), "target out of range")
    run(d(target=60))
    run(d(target=1440))


@pytest.mark.parametrize("v", [True, False, 1.0, 1.5, None, "1", [1], {}])
def test_nonint(v):
    bad(d(target=v), "target must be an int")
    x = d()
    x["nights"] = [[v, 5]]
    bad(x, "bedtime must be an int")
    x["nights"] = [[5, v]]
    bad(x, "waketime must be an int")


@pytest.mark.parametrize("v", [True, False, 1, 1.5, None, "ab", {}, ("a",)])
def test_noncontainer(v):
    x = d()
    x["nights"] = v
    bad(x, NI)
    x["nights"] = [v]
    bad(x, "night must be a [bedtime, waketime] pair")
    for p in ([1], [1, 2, 3]):
        x["nights"] = [p]
        bad(x, "night must be a [bedtime, waketime] pair")


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("nights", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    for k in ("nights", "target"):
        x = d()
        del x[k]
        bad(x, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["health_claim"] = True
    a["durations"].append(1)
    r = run(x)
    assert r["claims"]["health_claim"] is False and len(r["durations"]) == 3 and m.CLAIMS["health_claim"] is False


class SubInt(int):
    pass


class Quirky(int):
    """int subclass whose arithmetic lies: the auditor's witness for the +720 mutant."""
    def __sub__(self, other):
        return 0

    def __add__(self, other):
        return 1


def test_int_subclasses_refused_in_every_slot():
    for v in (SubInt(5), Quirky(0)):
        bad(d([[v, 1], [720, 721]], 60), "bedtime must be an int")
        bad(d([[0, v]], 60), "waketime must be an int")
        bad(d(target=v), "target must be an int")
        bad(d([[720, 721], [v, 1]], 60), "bedtime must be an int")
