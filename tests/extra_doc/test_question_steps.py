import copy
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import question_steps as m
from sugarcode.extra_doc.question_steps import StepsError, question_steps as run

KEYS = "data keys must be exactly steps"
NS = "steps must be a list of 1 to 12 steps"
ES = "each step must be a list of [questions, solved]"


def d(steps=((3, 0), (5, 0), (2, 1), (4, 1))):
    return {"steps": [list(e) for e in steps]}


def bad(data, msg):
    with pytest.raises(StepsError) as e:
        run(data)
    assert str(e.value) == msg


def oracle(x):
    """Independent: index scan with explicit accumulators."""
    st = x["steps"]
    total = 0
    solved = 0
    first = None
    before = 0
    for i, (q, s) in enumerate(st):
        total += q
        if s == 1:
            solved += 1
            if first is None:
                first = i
                before = total - q
    return total, solved, first, (None if first is None else before), (None if not solved else F(total, solved))


def check(x):
    o = run(x)
    total, solved, first, before, per = oracle(x)
    assert (o["total_questions"], o["solved_steps"], o["first_solved"], o["questions_before_solve"]) == (total, solved, first, before)
    assert (o["questions_per_solved_step"] is None) == (per is None)
    if per is not None:
        assert F(o["questions_per_solved_step"]) == per
    return o


def test_hand_worked():
    o = run(d())
    assert o["total_questions"] == 14 and o["solved_steps"] == 2 and o["first_solved"] == 2
    assert o["questions_before_solve"] == 8 and o["questions_per_solved_step"] == "7"
    assert o["status"] == "completed"
    assert o["claims"] == {"happened": False, "questions_led_to_solution": False, "sound_judgement": False, "real_world": False}
    assert len(o["not_claimed"]) == 4
    check(d())


def test_cases():
    o = run(d([(2, 0), (3, 0)]))
    assert o["first_solved"] is None and o["questions_before_solve"] is None and o["questions_per_solved_step"] is None
    assert o["total_questions"] == 5 and o["solved_steps"] == 0
    o = run(d([(7, 1)]))
    assert o["first_solved"] == 0 and o["questions_before_solve"] == 0 and o["questions_per_solved_step"] == "7"
    o = run(d([(1, 1), (2, 0), (2, 1)]))
    assert o["first_solved"] == 0 and o["questions_per_solved_step"] == "5/2"
    o = run(d([(0, 0), (0, 1)]))
    assert o["questions_before_solve"] == 0 and o["questions_per_solved_step"] == "0"
    o = run(d([(20, 0)] * 11 + [(20, 1)]))
    assert o["total_questions"] == 240 and o["questions_before_solve"] == 220 and o["questions_per_solved_step"] == "240"


def test_random():
    rng = random.Random(899)
    for _ in range(500):
        check(d([(rng.randint(0, 5), rng.randint(0, 1)) for _ in range(rng.randint(1, 12))]))


def test_caps():
    run(d([(1, 0)] * 12))
    bad(d([(1, 0)] * 13), NS)
    bad(d([(1, 0)] * 10**5), NS)
    bad(d([]), NS)


@pytest.mark.parametrize("v", [True, 1, 1.5, None, "ab", {}, (([1, 0]),)])
def test_noncontainers(v):
    bad({"steps": v}, NS)


@pytest.mark.parametrize("s", [None, 1, "ab", [1], [1, 0, 1], [], (1, 0), {}, True])
def test_bad_step(s):
    x = d()
    x["steps"][1] = s
    bad(x, ES)


@pytest.mark.parametrize("s", [True, False, 1.0, "5", None, [1], b"5"])
def test_nonint(s):
    for pos in (0, 1):
        x = d()
        x["steps"][1][pos] = s
        bad(x, "questions and solved must be ints")


@pytest.mark.parametrize("s", [-1, 21, 10**30, -(10**30)])
def test_questions_range(s):
    x = d()
    x["steps"][0][0] = s
    bad(x, "questions must be 0 to 20")


@pytest.mark.parametrize("s", [2, -1, 10**30])
def test_solved_range(s):
    x = d()
    x["steps"][0][1] = s
    bad(x, "solved must be 0 or 1")


@pytest.mark.parametrize("s", [0, 20])
def test_edges(s):
    check(d([(s, 0), (s, 1)]))


@pytest.mark.parametrize("x", [None, 1, "a", [], True, [("steps", 1)]])
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
    c = run(x)
    assert c["claims"]["real_world"] is False and c["total_questions"] == 14
    assert len(m.NOT_CLAIMED) == 4 and all(v is False for v in m.CLAIMS.values())


class _SubInt(int):
    pass


class _Quirky(int):
    """int subclass with lying arithmetic and comparisons."""
    def __sub__(self, o):
        return 0

    def __add__(self, o):
        return 1

    def __mul__(self, o):
        return 0

    def __gt__(self, o):
        return False

    def __lt__(self, o):
        return False


def _int_paths(x, path=()):
    if type(x) is int:
        yield path
    elif isinstance(x, dict):
        for k in x:
            yield from _int_paths(x[k], path + (k,))
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _int_paths(v, path + (i,))


def _put(x, path, val):
    y = copy.deepcopy(x)
    t = y
    for k in path[:-1]:
        t = t[k]
    t[path[-1]] = val
    return y


def test_int_subclasses_refused_in_every_int_slot():
    base = {"steps": [[3, 0], [5, 0], [2, 1], [4, 1]]}
    paths = list(_int_paths(base))
    assert paths
    for p in paths:
        for cls in (_SubInt, _Quirky):
            with pytest.raises(StepsError) as e:
                run(_put(base, p, cls(_get(base, p))))
            assert "must be an int" in str(e.value) or "must be ints" in str(e.value)


def _get(x, path):
    for k in path:
        x = x[k]
    return x


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
    base = {"steps": [[3, 0], [5, 0], [2, 1], [4, 1]]}
    n = 0
    for y in _variants(base):
        n += 1
        with pytest.raises(StepsError):
            run(y)
    assert n >= 2
