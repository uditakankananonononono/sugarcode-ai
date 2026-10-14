import itertools
import time
import pytest
from sugarcode.extra_doc.nim_solver import solve_nim as nim

T, V = TypeError, ValueError


def grundy(n, k):
    g = []
    for m in range(n + 1):
        seen = {g[m - t] for t in range(1, min(k, m) + 1)}
        x = 0
        while x in seen:
            x += 1
        g.append(x)
    return g


def oracle(piles, k):
    # Sprague-Grundy: a position is lost for the mover exactly when the XOR of the pile values is 0
    g = grundy(12, k)
    x = 0
    for p in piles:
        x ^= g[p]
    moves = []
    for i, n in enumerate(piles):
        for t in range(1, min(k, n) + 1):
            y = x ^ g[n] ^ g[n - t]
            if y == 0:
                moves.append([i, t])
    return {'winner': 'first' if x else 'second', 'winning_moves': moves, 'move': moves[0] if moves else None}


def test_hand_cases_exact():
    assert nim([3, 4, 5], 12) == {'winner': 'first', 'winning_moves': [[0, 2]], 'move': [0, 2]}
    assert nim([1, 1], 1) == {'winner': 'second', 'winning_moves': [], 'move': None}
    assert nim([0], 3) == {'winner': 'second', 'winning_moves': [], 'move': None}
    assert nim([0, 0, 0, 0], 1) == {'winner': 'second', 'winning_moves': [], 'move': None}
    assert nim([7], 3) == {'winner': 'first', 'winning_moves': [[0, 3]], 'move': [0, 3]}
    assert nim([8], 3)['winner'] == 'second'                   # 8 is a multiple of 3 + 1
    assert nim([1, 2, 3], 12) == {'winner': 'second', 'winning_moves': [], 'move': None}
    assert nim([1], 1) == {'winner': 'first', 'winning_moves': [[0, 1]], 'move': [0, 1]}
    r = nim([5, 5], 4)
    assert r['winner'] == 'second'
    r = nim([6, 5], 12)
    assert r['winning_moves'] == [[0, 1]] and r['move'] == [0, 1]


def test_all_small_positions_vs_sprague_grundy():
    n = 0
    for k in (1, 2, 3, 5, 12):
        for piles in itertools.product(range(0, 8), repeat=3):
            assert nim(list(piles), k) == oracle(list(piles), k)
            n += 1
    for k in (1, 2, 4):
        for piles in itertools.product(range(0, 5), repeat=4):
            assert nim(list(piles), k) == oracle(list(piles), k)
            n += 1
    assert n > 2000


def test_largest_position_is_fast_and_matches():
    t0 = time.time()
    for k in (1, 2, 12):
        assert nim([12, 12, 12, 12], k) == oracle([12, 12, 12, 12], k)
        assert nim([12, 11, 10, 9], k) == oracle([12, 11, 10, 9], k)
    assert time.time() - t0 < 20
    assert nim([12, 12, 12, 12], 12)['winner'] == 'second'


def test_input_forms_and_not_mutated():
    p = [2, 3]
    assert nim(tuple(p), 2) == nim(p, 2) and p == [2, 3]


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


def test_pins():
    err(nim, T, 'piles must be a list or tuple', 'ab', 1)
    err(nim, T, 'piles must be a list or tuple', {1}, 1)
    err(nim, V, 'pile count must be between 1 and 4', [], 1)
    err(nim, V, 'pile count must be between 1 and 4', [1] * 5, 1)
    for bad in (True, 1.0, '1', None):
        err(nim, T, 'pile must be a nonbool int', [1, bad], 1)
        err(nim, T, 'max_take must be a nonbool int', [1], bad)
    err(nim, V, 'pile must be between 0 and 12', [-1], 1)
    err(nim, V, 'pile must be between 0 and 12', [13], 1)
    err(nim, V, 'max_take must be between 1 and 12', [1], 0)
    err(nim, V, 'max_take must be between 1 and 12', [1], 13)


def test_edges_accepted():
    nim([0], 1)
    nim([12] * 4, 1)
    nim([12], 12)
    assert nim([12], 12)['move'] == [0, 12]


def test_order_and_every_position():
    err(nim, T, 'piles must be a list or tuple', 'x', 'y')
    err(nim, V, 'pile count must be between 1 and 4', [], 'y')
    err(nim, V, 'pile must be between 0 and 12', [13], 'y')
    err(nim, V, 'pile must be between 0 and 12', [13, True], 99)
    for pos in range(4):
        p = [1, 2, 3, 4]
        p[pos] = 1.5
        err(nim, T, 'pile must be a nonbool int', p, 2)
        p[pos] = 13
        err(nim, V, 'pile must be between 0 and 12', p, 2)


class IntSub(int):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def test_subclass_witnesses_are_rejected_with_exact_errors():
    err(nim, T, 'piles must be a list or tuple', ListSub([1, 2]), 1)
    err(nim, T, 'piles must be a list or tuple', TupleSub([1, 2]), 1)
    err(nim, T, 'pile must be a nonbool int', [1, IntSub(2)], 1)
    err(nim, T, 'pile must be a nonbool int', [IntSub(1)], 1)
    err(nim, T, 'max_take must be a nonbool int', [1], IntSub(1))
    # plain types still work and give the same answer as the subclass-free form
    assert nim([1, 2], 1) == nim((1, 2), 1)
