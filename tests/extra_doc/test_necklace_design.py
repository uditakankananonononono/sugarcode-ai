import random
from itertools import permutations
import pytest
from sugarcode.extra_doc.necklace_design import check_necklace as chk, graduated_symmetric as gs


def oracle_chk(b, clasp, target, tol):
    n = len(b)
    # graduated per the module's definition: the peak is the middle bead (the LEFT middle bead for even n)
    peaks = [(n - 1) // 2] if n % 2 else [n // 2 - 1]
    grad = any(all(b[i] <= b[i + 1] for i in range(p)) and all(b[i] >= b[i + 1] for i in range(p, n - 1)) for p in peaks)
    L = sum(b) + clasp
    return dict(length_mm=L, gap_mm=L - target, within_tolerance=-tol <= L - target <= tol,
                symmetric=all(b[i] == b[n - 1 - i] for i in range(n)), graduated=grad, bead_count=n)


def test_check_random():
    rnd = random.Random(1)
    for _ in range(500):
        n = rnd.randint(1, 8)
        b = [rnd.randint(1, 5) for _ in range(n)]
        if rnd.random() < .4:
            h = sorted(b[: n // 2])
            b = h + ([rnd.randint(5, 6)] if n % 2 else []) + h[::-1]
        c, t, tol = rnd.randint(0, 20), rnd.randint(1, 60), rnd.randint(0, 10)
        assert chk(b, c, t, tol) == oracle_chk(b, c, t, tol)


def test_gs_vs_bruteforce():
    rnd = random.Random(2)
    for _ in range(300):
        n = rnd.randint(1, 7)
        b = [rnd.randint(1, 4) for _ in range(n)]
        ok = []
        for p in set(permutations(b)):
            p = list(p)
            if p == p[::-1] and oracle_chk(p, 0, 1, 0)['graduated']:
                ok.append(p)
        r = gs(b)
        assert r['possible'] == bool(ok)
        if ok:
            assert len(ok) == 1 and r['arrangement'] == ok[0]
        else:
            assert r['arrangement'] is None
        assert r['odd_sizes'] == sorted(k for k in set(b) if b.count(k) % 2)


def test_hand_cases():
    r = chk([3, 5, 8, 5, 3], 10, 40, 2)
    assert r == {'length_mm': 34, 'gap_mm': -6, 'within_tolerance': False, 'symmetric': True, 'graduated': True, 'bead_count': 5}
    assert chk([3, 5, 8, 5, 3], 10, 40, 6)['within_tolerance'] is True
    assert chk([3, 5, 8, 5, 3], 10, 28, 6)['within_tolerance'] is True
    assert chk([3, 5, 8, 5, 3], 10, 28, 5)['within_tolerance'] is False
    assert chk([5, 3, 5], 0, 13, 0)['graduated'] is False and chk([5, 3, 5], 0, 13, 0)['symmetric'] is True
    assert chk([1, 2, 3], 0, 6, 0)['graduated'] is False and chk([1, 2, 3], 0, 6, 0)['symmetric'] is False
    assert chk([1, 2, 2, 1], 0, 6, 0)['graduated'] is True
    assert chk([1, 2, 3, 1], 0, 6, 0)['graduated'] is False
    assert chk([1, 3, 2, 1], 0, 6, 0)['graduated'] is True
    assert chk([7], 0, 7, 0) == {'length_mm': 7, 'gap_mm': 0, 'within_tolerance': True, 'symmetric': True, 'graduated': True, 'bead_count': 1}
    assert gs([3, 5, 5, 3, 8]) == {'possible': True, 'arrangement': [3, 5, 8, 5, 3], 'odd_sizes': [8]}
    assert gs([3, 5, 5]) == {'possible': False, 'arrangement': None, 'odd_sizes': [3]}
    assert gs([4, 4]) == {'possible': True, 'arrangement': [4, 4], 'odd_sizes': []}
    assert gs([4, 5]) == {'possible': False, 'arrangement': None, 'odd_sizes': [4, 5]}
    assert gs([9]) == {'possible': True, 'arrangement': [9], 'odd_sizes': [9]}
    assert gs([1, 1, 2]) == {'possible': True, 'arrangement': [1, 2, 1], 'odd_sizes': [2]}


def test_caps_accept():
    chk([30] * 24, 100, 2000, 200)
    chk([1], 0, 1, 0)
    gs([30] * 24)
    gs((1,))


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


T, V = TypeError, ValueError


def test_pins():
    for f, rest in ((chk, (0, 1, 0)), (gs, ())):
        err(f, T, 'beads must be a list or tuple', 'ab', *rest)
        err(f, V, 'bead count must be between 1 and 24', [], *rest)
        err(f, V, 'bead count must be between 1 and 24', [1] * 25, *rest)
        for bad in (True, 1.0, '1', None):
            err(f, T, 'bead size must be a nonbool int', [1, bad], *rest)
        err(f, V, 'bead size must be between 1 and 30 mm', [0], *rest)
        err(f, V, 'bead size must be between 1 and 30 mm', [31], *rest)
        for pos in range(3):
            b = [1, 1, 1]
            b[pos] = 31
            err(f, V, 'bead size must be between 1 and 30 mm', b, *rest)
    B = [1]
    for i, nm in enumerate(('clasp_mm', 'target_mm', 'tolerance_mm')):
        for bad in (True, 1.0, None):
            a = [0, 1, 0]
            a[i] = bad
            err(chk, T, nm + ' must be a nonbool int', B, *a)
    err(chk, V, 'clasp_mm must be between 0 and 100', B, -1, 1, 0)
    err(chk, V, 'clasp_mm must be between 0 and 100', B, 101, 1, 0)
    err(chk, V, 'target_mm must be between 1 and 2000', B, 0, 0, 0)
    err(chk, V, 'target_mm must be between 1 and 2000', B, 0, 2001, 0)
    err(chk, V, 'tolerance_mm must be between 0 and 200', B, 0, 1, -1)
    err(chk, V, 'tolerance_mm must be between 0 and 200', B, 0, 1, 201)


def test_validation_even_when_unsatisfiable():
    err(gs, T, 'bead size must be a nonbool int', [1, 2, 3, None])
    err(chk, V, 'tolerance_mm must be between 0 and 200', [1, 2, 3], 0, 1000, 999)
