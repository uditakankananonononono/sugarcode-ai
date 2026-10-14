import copy
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc import autoscale_run as m
from sugarcode.extra_doc.autoscale_run import ScaleError, autoscale_run as run


EXPECTED_NOT_CLAIMED = ['this adjusts any real capacity', 'the policy is a good one', 'a load list matches real traffic', 'real-world outcome']
BASE = {"loads": [100, 100, 10, 10, 10, 10], "capacity": 50, "min_replicas": 1, "max_replicas": 5, "start": 1, "down_ticks": 2}


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
        with pytest.raises(ScaleError):
            run(_swap(BASE, p, _D if kind == "d" else _L))
