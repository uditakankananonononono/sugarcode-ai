import copy
import random

import pytest

from sugarcode.extra_doc import experience_cycles as m
from sugarcode.extra_doc.experience_cycles import CycleError, experience_cycles as run

KEYS = "data keys must be exactly log"
NL = "log must be a list of 1 to 16 stages"
ST = "stage must be one of experience, reflect, conceptualize, experiment"
EX, RE, CO, XP = "experience", "reflect", "conceptualize", "experiment"
ORDER = [EX, RE, CO, XP]


def d(log=(EX, RE, CO, XP, EX, XP, RE)):
    return {"log": list(log)}


def bad(data, msg):
    with pytest.raises(CycleError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: repeated subsequence search with list.index from a moving start."""
    log = x["log"]
    pos = 0
    cycles = 0
    while True:
        p = pos
        ok = True
        for st in ORDER:
            if st in log[p:]:
                p = log.index(st, p) + 1
            else:
                ok = False
                break
        if not ok:
            break
        cycles += 1
        pos = p
    return cycles


def check(x):
    o = run(x)
    # the stage-by-stage scan and the subsequence search agree on the cycle count
    assert o["cycles"] == oracle(x)
    assert sum(o["stages_seen"].values()) == len(x["log"])
    assert o["next_needed"] in ORDER
    assert 0 <= o["set_aside"] <= len(x["log"])
    return o


def test_hand_worked():
    o = run(d())
    assert o["cycles"] == 1 and o["next_needed"] == CO and o["set_aside"] == 1
    assert o["stages_seen"] == {CO: 1, EX: 2, XP: 2, RE: 2}
    assert list(o["stages_seen"]) == sorted(o["stages_seen"])
    assert o["status"] == "completed"
    assert o["claims"] == {"real_record": False, "cycle_is_learning": False, "only_valid_order": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d(ORDER * 4))
    assert o["cycles"] == 4 and o["next_needed"] == EX and o["set_aside"] == 0
    o = run(d([XP, CO, RE, EX]))
    assert o["cycles"] == 0 and o["next_needed"] == RE and o["set_aside"] == 3
    o = run(d([EX]))
    assert o["cycles"] == 0 and o["next_needed"] == RE and o["set_aside"] == 0
    o = run(d([RE]))
    assert o["next_needed"] == EX and o["set_aside"] == 1
    o = run(d([EX, EX, RE, RE, CO, CO, XP, XP]))
    assert o["cycles"] == 1 and o["set_aside"] == 4 and o["next_needed"] == EX
    o = run(d([EX, RE, CO]))
    assert o["next_needed"] == XP and o["cycles"] == 0
    o = run(d([EX, RE, CO, XP, EX, RE, CO, XP, EX]))
    assert o["cycles"] == 2 and o["next_needed"] == RE


def test_random():
    rng = random.Random(897)
    for _ in range(800):
        check(d([rng.choice(ORDER) for _ in range(rng.randint(1, 16))]))


def test_caps():
    run(d([EX] * 16))
    bad(d([EX] * 17), NL)
    bad(d([EX] * 10**5), NL)
    bad(d([]), NL)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (EX,)])
def test_noncontainers(v):
    bad({"log": v}, NL)


@pytest.mark.parametrize("s", ["", "Experience", "experience ", "x", None, 1, True, b"experience", [EX]])
def test_bad_stage(s):
    bad(d([EX, s]), ST)
    bad(d([s]), ST)


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("log", 1)]])
def test_data_not_dict(x):
    bad(x, KEYS)


def test_keys_exact():
    bad({}, KEYS)
    x = d()
    x["extra"] = 1
    bad(x, KEYS)


def test_no_mutation_determinism_fresh_claims():
    x = d()
    y = copy.deepcopy(x)
    a, b = run(x), run(x)
    assert x == y and a == b
    a["claims"]["real_world"] = True
    a["stages_seen"][EX] = 99
    c = run(x)
    assert c["claims"]["real_world"] is False and c["stages_seen"][EX] == 2
    assert len(m.NOT_CLAIMED) == 4 and all(v is False for v in m.CLAIMS.values())


class _SubStr(str):
    pass


class _LyingStr(str):
    """str subclass that hashes like 1 and equals 1."""
    def __hash__(self):
        return 1

    def __eq__(self, o):
        return o == 1 or str.__eq__(self, o)


def _variants(x):
    """Yield every copy of x with one str leaf or one dict key replaced by bytes or a str subclass."""
    import copy as _c
    def walk(node, path):
        if type(node) is str:
            yield path, "leaf"
        elif isinstance(node, dict):
            for k in node:
                if type(k) is str:
                    yield path + (k,), "key"
                yield from walk(node[k], path + (k,))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, path + (i,))
    for path, kind in walk(x, ()):
        for mk in (lambda s: s.encode(), _SubStr, _LyingStr):
            if kind == "key" and mk is _SubStr:
                continue   # a plain str subclass hashes and compares like its key: indistinguishable as a dict key
            y = _c.deepcopy(x)
            t = y
            for k in path[:-1]:
                t = t[k]
            last = path[-1]
            if kind == "leaf":
                t[last] = mk(t[last])
            else:
                t2 = {}
                for k, v in t.items():
                    t2[mk(k) if k == last else k] = v
                if len(path) == 1:
                    y = t2
                else:
                    u = y
                    for k in path[:-2]:
                        u = u[k]
                    u[path[-2]] = t2
            yield y


def test_nonexact_str_refused_in_every_str_slot_and_key():
    base = {"log": ["experience", "reflect", "conceptualize", "experiment"]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(CycleError):
            run(y)
    assert n >= 2
