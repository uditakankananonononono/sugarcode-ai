import copy
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import fault_vote as m
from sugarcode.extra_doc.fault_vote import VoteError, fault_vote as run


EXPECTED_NOT_CLAIMED = ['this makes any system fault tolerant', 'f faults of a real kind are covered', 'replica answers are independent', 'real-world outcome']
BASE = {"results": [7, 7, 9], "f": 1}


def test_not_claimed_text_pinned_per_entry():
    assert [str(x) for x in m.NOT_CLAIMED] == EXPECTED_NOT_CLAIMED
    assert type(m.NOT_CLAIMED) in (tuple, list)
    for entry, want in zip(m.NOT_CLAIMED, EXPECTED_NOT_CLAIMED):
        assert type(entry) is str and entry == want
    o = run(copy.deepcopy(BASE))
    assert o["not_claimed"] == EXPECTED_NOT_CLAIMED
    assert len(o["not_claimed"]) == len(EXPECTED_NOT_CLAIMED)
    o["not_claimed"][0] += "x"
    assert run(copy.deepcopy(BASE))["not_claimed"] == EXPECTED_NOT_CLAIMED


class _D(dict):
    pass


class _L(list):
    pass


def _containers(x, path=()):
    if type(x) is dict:
        yield path, "d"
        for k in x:
            yield from _containers(x[k], path + (k,))
    elif type(x) is list:
        yield path, "l"
        for i, v in enumerate(x):
            yield from _containers(v, path + (i,))


def _swap(x, path, cls):
    y = copy.deepcopy(x)
    if not path:
        return cls(y)
    t = y
    for k in path[:-1]:
        t = t[k]
    t[path[-1]] = cls(t[path[-1]])
    return y


def test_container_subclasses_refused_at_every_container():
    paths = list(_containers(BASE))
    assert paths and paths[0] == ((), "d")
    for p, kind in paths:
        with pytest.raises(VoteError):
            run(_swap(BASE, p, _D if kind == "d" else _L))
