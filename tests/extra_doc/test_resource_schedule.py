import itertools
import random
import time
import pytest
from sugarcode.extra_doc.resource_schedule import assign_tasks as at

T, V = TypeError, ValueError


def oracle(ds, m):
    best, pick = None, None
    for a in itertools.product(range(m), repeat=len(ds)):          # lexicographic order
        seen = -1
        ok = True
        for x in a:
            if x > seen + 1:
                ok = False
                break
            seen = max(seen, x)
        if not ok:
            continue
        loads = [0] * m
        for d, x in zip(ds, a):
            loads[x] += d
        mk = max(loads)
        if best is None or mk < best:
            best, pick = mk, (list(a), loads)
    return {'makespan': best, 'assignment': pick[0], 'loads': pick[1]}


def test_hand_cases_exact():
    assert at([3, 3, 2, 2, 2], 2) == {'makespan': 6, 'assignment': [0, 0, 1, 1, 1], 'loads': [6, 6]}
    assert at([5], 3) == {'makespan': 5, 'assignment': [0], 'loads': [5, 0, 0]}
    assert at([4, 3, 3, 2, 2, 1], 3) == {'makespan': 5, 'assignment': [0, 1, 2, 1, 2, 0], 'loads': [5, 5, 5]}
    assert at([7, 7, 7], 1) == {'makespan': 21, 'assignment': [0, 0, 0], 'loads': [21]}
    assert at([4, 4, 4], 3) == {'makespan': 4, 'assignment': [0, 1, 2], 'loads': [4, 4, 4]}
    # a plain greedy (longest first onto the lightest machine) gives 14 here, the optimum is 12
    assert at([5, 5, 4, 4, 3, 3, 3, 3], 3)['makespan'] == 10
    assert at([3, 3, 2, 2, 2], 2)['makespan'] == 6
    # more machines than tasks never helps beyond the longest task
    r = at([9, 1], 5)
    assert r == {'makespan': 9, 'assignment': [0, 1], 'loads': [9, 1, 0, 0, 0]}


def test_random_vs_oracle():
    rnd = random.Random(573)
    split = 0
    for _ in range(300):
        n = rnd.randint(1, 7)
        m = rnd.randint(1, 4)
        ds = [rnd.randint(1, 9) for _ in range(n)]
        got = at(ds, m)
        want = oracle(ds, m)
        assert got == want
        split += len(set(want['assignment'])) > 1
    assert split > 100


def test_tuple_input_and_input_not_mutated():
    ds = [3, 1, 2]
    r = at(tuple(ds), 2)
    assert ds == [3, 1, 2] and r == at(ds, 2)


def test_largest_case_is_fast_and_exact_makespan():
    t0 = time.time()
    r = at([1000, 999, 998, 997, 996, 995, 994, 993, 992, 991], 5)
    assert time.time() - t0 < 5
    assert r['makespan'] == 1991              # five pairs summing to 1991 meet the lower bound ceil(9955 / 5)
    assert max(r['loads']) == r['makespan'] and sum(r['loads']) == 9955
    r = at([1000] * 10, 3)
    assert r['makespan'] == 4000 and r['loads'] == [4000, 4000, 2000] and r['assignment'] == [0] * 4 + [1] * 4 + [2] * 2
    r = at([1] * 10, 5)
    assert r['makespan'] == 2 and r['assignment'] == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


def test_pins():
    err(at, T, 'durations must be a list or tuple', 'ab', 1)
    err(at, T, 'durations must be a list or tuple', {1}, 1)
    err(at, V, 'task count must be between 1 and 10', [], 1)
    err(at, V, 'task count must be between 1 and 10', [1] * 11, 1)
    for bad in (True, 1.0, '1', None, 2.5):
        err(at, T, 'duration must be a nonbool int', [1, bad], 1)
        err(at, T, 'machines must be a nonbool int', [1], bad)
    err(at, V, 'duration must be between 1 and 1000', [0], 1)
    err(at, V, 'duration must be between 1 and 1000', [1, -5], 1)
    err(at, V, 'duration must be between 1 and 1000', [1001], 1)
    err(at, V, 'machines must be between 1 and 5', [1], 0)
    err(at, V, 'machines must be between 1 and 5', [1], 6)
    err(at, V, 'machines must be between 1 and 5', [1], -1)


def test_edges_accepted():
    at([1] * 10, 1)
    at([1000], 5)
    at([1], 5)
    assert at([1000], 1)['makespan'] == 1000 and at([1], 1)['makespan'] == 1


def test_order_and_every_position():
    err(at, T, 'durations must be a list or tuple', 'x', 'y')
    err(at, V, 'task count must be between 1 and 10', [], 'y')
    err(at, V, 'duration must be between 1 and 1000', [0], 'y')
    err(at, T, 'duration must be a nonbool int', [True, 0], 99)
    err(at, V, 'duration must be between 1 and 1000', [0, True], 99)   # the first problem in order is the range error of 0
    for pos in range(3):
        ds = [1, 2, 3]
        ds[pos] = 2.5
        err(at, T, 'duration must be a nonbool int', ds, 2)
        ds[pos] = 1001
        err(at, V, 'duration must be between 1 and 1000', ds, 2)
