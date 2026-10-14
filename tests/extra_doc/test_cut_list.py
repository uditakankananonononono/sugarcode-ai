import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.cut_list import cut_plan, tip_check


def rgs(n):
    def rec(pre, mx):
        if len(pre) == n:
            yield tuple(pre)
            return
        for v in range(mx + 2):
            yield from rec(pre + [v], max(mx, v))
    yield from rec([0], 0)


def oracle(parts, stock, kerf):
    n = len(parts)
    best = None
    for p in rgs(n):
        k = max(p) + 1
        loads = [0] * k
        for i, b in enumerate(p):
            loads[b] += parts[i] + kerf
        if max(loads) <= stock:
            key = (k, p)
            if best is None or key < best:
                best = key
    return best


def test_random_vs_bruteforce():
    rnd = random.Random(4)
    for _ in range(300):
        n = rnd.randint(1, 7)
        stock = rnd.randint(10, 60)
        kerf = rnd.randint(0, 4)
        parts = [rnd.randint(1, stock - kerf) for _ in range(n)]
        k, asg = oracle(parts, stock, kerf)
        r = cut_plan(parts, stock, kerf)
        assert r['boards'] == k and r['assignment'] == list(asg)
        assert [sorted(b) for b in r['board_parts']] == [[i for i in range(n) if asg[i] == b] for b in range(k)]
        used = [sum(parts[i] + kerf for i in b) for b in r['board_parts']]
        assert r['waste_mm'] == [stock - u for u in used] and r['total_waste_mm'] == stock * k - sum(used)


def test_hand_cases():
    r = cut_plan([800, 600, 600, 400, 400], 1500, 3)
    assert r == {'boards': 2, 'assignment': [0, 0, 1, 1, 1], 'board_parts': [[0, 1], [2, 3, 4]],
                 'waste_mm': [94, 91], 'total_waste_mm': 185}
    # kerf decides: 3 parts of 49 on a 100 board: kerf 1 -> 50+50 fits two, third needs a second board
    assert cut_plan([49, 49, 49], 100, 1)['boards'] == 2
    assert cut_plan([49, 49, 49], 100, 0)['boards'] == 2
    assert cut_plan([50, 50], 100, 0)['boards'] == 1
    assert cut_plan([50, 50], 100, 1)['boards'] == 2
    assert cut_plan([99], 100, 1)['assignment'] == [0]
    parts = [44, 24, 24, 22, 21, 21, 20, 12]
    r = cut_plan(parts, 100, 0)
    k, asg = oracle(parts, 100, 0)
    assert r['boards'] == k and r['assignment'] == list(asg)


def test_twelve_parts_accepted_and_fast():
    r = cut_plan([5000] * 12, 10000, 0)
    assert r['boards'] == 6 and r['total_waste_mm'] == 0
    r = cut_plan([1] * 12, 10000, 20)
    assert r['boards'] == 1 and r['assignment'] == [0] * 12
    r = cut_plan([3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4], 14, 0)
    assert r['boards'] == 3 and r['total_waste_mm'] == 0


def test_tip_check():
    r = tip_check(400, 700, 300, 150)
    assert r == {'margin_mm': F(50), 'load_over_base': True, 'load_within_height': True, 'stable': True}
    assert tip_check(400, 700, 300, 200)['margin_mm'] == 0 and tip_check(400, 700, 300, 200)['load_over_base'] is True
    assert tip_check(400, 700, 300, 201)['load_over_base'] is False and tip_check(400, 700, 300, 201)['stable'] is False
    assert tip_check(401, 700, 300, 200)['margin_mm'] == F(1, 2)
    assert tip_check(400, 700, 700, 0)['load_within_height'] is True
    r = tip_check(400, 700, 701, 0)
    assert r['load_within_height'] is False and r['stable'] is False and r['load_over_base'] is True
    tip_check(5000, 5000, 5000, 5000)
    tip_check(1, 1, 0, 0)


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


T, V = TypeError, ValueError


def test_pins_cut_plan():
    err(cut_plan, T, 'parts must be a list or tuple', 'a', 10, 0)
    err(cut_plan, V, 'part count must be between 1 and 12', [], 10, 0)
    err(cut_plan, V, 'part count must be between 1 and 12', [1] * 13, 10, 0)
    for bad in (True, 1.0, None):
        err(cut_plan, T, 'part length must be a nonbool int', [1, bad], 10, 0)
        err(cut_plan, T, 'stock_mm must be a nonbool int', [1], bad, 0)
        err(cut_plan, T, 'kerf_mm must be a nonbool int', [1], 10, bad)
    for bad in (0, 5001):
        err(cut_plan, V, 'part length must be between 1 and 5000 mm', [1, bad], 10, 0)
    err(cut_plan, V, 'stock_mm must be between 1 and 10000', [1], 0, 0)
    err(cut_plan, V, 'stock_mm must be between 1 and 10000', [1], 10001, 0)
    err(cut_plan, V, 'kerf_mm must be between 0 and 20', [1], 10, -1)
    err(cut_plan, V, 'kerf_mm must be between 0 and 20', [1], 10, 21)
    err(cut_plan, V, 'a part plus its kerf is longer than the stock board', [10], 10, 1)
    err(cut_plan, V, 'a part plus its kerf is longer than the stock board', [1, 5, 1], 5, 1)
    cut_plan([9], 10, 1)
    for pos in range(3):
        p = [1, 1, 1]
        p[pos] = None
        err(cut_plan, T, 'part length must be a nonbool int', p, 1, 0)


def test_pins_tip_check():
    for i, nm in enumerate(('base_mm', 'height_mm', 'load_height_mm', 'load_offset_mm')):
        for bad in (True, 1.0, None):
            a = [1, 1, 0, 0]
            a[i] = bad
            err(tip_check, T, nm + ' must be a nonbool int', *a)
    err(tip_check, V, 'base_mm must be between 1 and 5000', 0, 1, 0, 0)
    err(tip_check, V, 'base_mm must be between 1 and 5000', 5001, 1, 0, 0)
    err(tip_check, V, 'height_mm must be between 1 and 5000', 1, 0, 0, 0)
    err(tip_check, V, 'height_mm must be between 1 and 5000', 1, 5001, 0, 0)
    err(tip_check, V, 'load_height_mm must be between 0 and 5000', 1, 1, -1, 0)
    err(tip_check, V, 'load_height_mm must be between 0 and 5000', 1, 1, 5001, 0)
    err(tip_check, V, 'load_offset_mm must be between 0 and 5000', 1, 1, 0, -1)
    err(tip_check, V, 'load_offset_mm must be between 0 and 5000', 1, 1, 0, 5001)
    err(tip_check, T, 'height_mm must be a nonbool int', 0, 1.5, 0, 0)  # types before ranges


def test_range_edges_and_stability_edges():
    assert cut_plan([1], 1, 0)['boards'] == 1
    assert cut_plan([5000, 5000], 10000, 0)['boards'] == 1
    assert cut_plan([1], 10000, 0)['boards'] == 1
    r = tip_check(400, 700, 300, 200)             # margin exactly 0 is still over the base
    assert r['stable'] is True and r['margin_mm'] == 0
    r = tip_check(400, 700, 700, 100)             # load exactly as high as the piece is allowed
    assert r['stable'] is True and r['load_within_height'] is True
    assert tip_check(400, 700, 701, 100)['stable'] is False
    assert tip_check(400, 700, 300, 201)['stable'] is False
    assert tip_check(1, 1, 1, 0)['stable'] is True
