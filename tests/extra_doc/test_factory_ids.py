import re
import pytest
from sugarcode.extra_doc import factory_ids as fi

P = fi.produce
NC = ("an implementation of the pattern", "object creation", "design quality",
      "runtime behaviour", "uniqueness across processes")
NM = "name of a-z, 0-9, _ (1 to 30, starting with a letter) required"


class I(int):
    pass


class Li(list):
    pass


class Tu(tuple):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        P(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def test_constants():
    assert (fi.MAX_KINDS, fi.MAX_COUNT, fi.MAX_TOTAL) == (16, 1000, 2000) and fi.NOT_CLAIMED == NC


def test_hand_literals():
    r = P([("car", 2), ("bike", 0), ("van", 3)])
    assert r["identifiers"] == ["car-0001", "car-0002", "van-0001", "van-0002", "van-0003"]
    assert r["total"] == 5
    assert P([("a", 1000)])["identifiers"][-1] == "a-1000"
    assert P([("a", 1000)])["identifiers"][0] == "a-0001"
    assert P([("x", 10)])["identifiers"][8:] == ["x-0009", "x-0010"]
    assert P([("x", 100)])["identifiers"][98:] == ["x-0099", "x-0100"]
    assert P([("z", 0)]) == {"identifiers": [], "total": 0, "factory_validated": False, "not_claimed": NC}


def test_shape_and_untouched():
    p = [("a", 1)]
    r = P(p)
    assert p == [("a", 1)]
    assert r == {"identifiers": ["a-0001"], "total": 1, "factory_validated": False, "not_claimed": NC}


def test_independent_oracle():
    import random
    rnd = random.Random(665)
    for _ in range(100):
        kinds = rnd.sample(["a", "b", "c_1", "d", "e2"], rnd.randint(1, 5))
        plan = [(k, rnd.randint(0, 12)) for k in kinds]
        want = []
        for k, c in plan:
            for n in range(c):
                want.append(k + "-" + str(n + 1).rjust(4, "0"))
        r = P(plan)
        assert r["identifiers"] == want and r["total"] == len(want)
        assert len(set(want)) == len(want)


def test_total_cap_boundary():
    r = P([("a", 1000), ("b", 1000)])
    assert r["total"] == 2000 and len(r["identifiers"]) == 2000
    refuse("plan: counts must add up to at most 2000", [("a", 1000), ("b", 1000), ("c", 1)])
    assert P([(f"k{i}", 125) for i in range(16)])["total"] == 2000
    refuse("plan: counts must add up to at most 2000", [(f"k{i}", 126) for i in range(16)])


def test_caps_accepted():
    assert P([("a" * 30, 1)])["identifiers"] == ["a" * 30 + "-0001"]
    assert P([(f"k{i}", 0) for i in range(16)])["total"] == 0


BAD = [None, 5, "", "A", "1a", "_a", "a-b", "a\n", "\u00e9", "a\u00e9", "\uff41", "a" * 31, St("a"), b"a"]


@pytest.mark.parametrize("bad", BAD)
def test_kind_refusals(bad):
    refuse(f"plan[0] kind: {NM}", [(bad, 1)])
    refuse(f"plan[1] kind: {NM}", [("a", 1), (bad, 1)])


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), -1, 1001])
def test_count_refusals(bad):
    refuse("plan[0] count: whole number 0 to 1000 required", [("a", bad)])
    refuse("plan[1] count: whole number 0 to 1000 required", [("a", 1), ("b", bad)])


@pytest.mark.parametrize("bad", [[], ("a",), ("a", 1, 2), Tu(("a", 1)), ["a", 1], None, "ab"])
def test_row_shape(bad):
    refuse("plan[0]: (kind, count) tuple required", [bad])
    refuse("plan[1]: (kind, count) tuple required", [("a", 1), bad])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([("a", 1)]), [], [(f"k{i}", 1) for i in range(17)]])
def test_plan_shape(bad):
    refuse("plan: list of 1 to 16 required", bad)


def test_distinct_and_order():
    refuse("plan: kinds must be distinct", [("a", 1), ("a", 2)])
    refuse("plan: list of 1 to 16 required", None)
    refuse("plan: kinds must be distinct", [("a", 1000), ("a", 1000), ("a", 1000)])
    refuse("plan[0] count: whole number 0 to 1000 required", [("a", -1), ("a", 1)])
