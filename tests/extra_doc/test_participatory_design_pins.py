"""Row 351 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import pytest

from sugarcode.extra_doc.participatory_design import participatory_vote as pv


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        pv(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'ballots and weights must be lists or tuples'
PC = 'participant count must be between 1 and 32'
CC = 'candidate_count must be a nonbool integer between 1 and 8'
WC = 'weight count must match participants'
BL = 'ballots must be lists or tuples no longer than candidate count'
BI = 'ballot indices must be nonbool integers inside candidate range'
BU = 'ballot candidates must be unique'
WT = 'weights must be nonbool integers zero through 1000000'


def oracle(ballots, weights, k):
    scores = [0] * k
    for b, w in zip(ballots, weights):
        for rank, c in enumerate(b):
            scores[c] += w * (k - rank)
    return scores


CASES = [
    ([[0, 1, 2], [1, 0, 2], [2]], [1, 1, 1], 3),
    ([[0], [1]], [3, 3], 2),
    ([[1, 0], [1], []], [2, 5, 9], 2),
    ([[2, 1, 0], [2, 1, 0]], [0, 0], 3),
    ([[0, 1, 2, 3, 4, 5, 6, 7]], [1000000], 8),
    ([[3], [0], [1], [2]], [1, 1, 1, 1], 4),
    ([[]], [5], 1),
]


@pytest.mark.parametrize('b,w,k', CASES)
def test_oracle(b, w, k):
    s = oracle(b, w, k)
    r = pv(b, w, k)
    assert r['scores'] == s and r['winner_indices'] == [i for i, v in enumerate(s) if v == max(s)]
    assert r['participant_contributions'] == [oracle([bb], [ww], k) for bb, ww in zip(b, w)]
    assert r['consultation_performed'] is False
    assert set(r) == {'scores', 'participant_contributions', 'winner_indices', 'consultation_performed'}


def test_literals_and_ties():
    r = pv([[0, 1, 2], [1, 0, 2], [2]], [1, 1, 1], 3)
    assert r == {'scores': [5, 5, 5], 'participant_contributions': [[3, 2, 1], [2, 3, 1], [0, 0, 3]],
                 'winner_indices': [0, 1, 2], 'consultation_performed': False}
    assert pv([[1]], [0], 2)['winner_indices'] == [0, 1]                  # all zero: everyone ties
    assert pv([[0, 1]], [7], 2)['scores'] == [14, 7]                      # top rank gets k points, not k-1
    assert pv([[1, 0]], [1], 2)['scores'] == [1, 2]
    assert pv([[0], [0]], [1000000, 1000000], 8)['scores'][0] == 16000000


def test_caps_n_and_n_plus_1():
    assert pv([[0]] * 32, [1] * 32, 1)['scores'] == [32]
    refuses(ValueError, PC, [[0]] * 33, [1] * 33, 1)
    refuses(ValueError, PC, [], [], 1)
    assert pv([[0]], [1], 8)['scores'][0] == 8
    for b in (0, 9, -1):
        refuses(ValueError, CC, [[0]], [1], b)
    refuses(ValueError, WC, [[0]], [1, 1], 1)
    refuses(ValueError, WC, [[0], [0]], [1], 1)
    assert pv([[0, 1]], [1], 2)['scores'] == [2, 1]
    refuses(ValueError, BL, [[0, 1, 2]], [1], 2)
    refuses(ValueError, BL, [[0], [0, 1, 2]], [1, 1], 2)
    for b in (-1, 2):
        refuses(ValueError, BI, [[b]], [1], 2)
        refuses(ValueError, BI, [[0], [0, b]], [1, 1], 2)
    refuses(ValueError, BU, [[0, 0]], [1], 2)
    refuses(ValueError, BU, [[0], [1, 1]], [1, 1], 2)
    for b in (-1, 1000001):
        refuses(ValueError, WT, [[0]], [b], 1)
        refuses(ValueError, WT, [[0], [0]], [1, b], 1)
    assert pv([[0]], [0], 1)['scores'] == [0] and pv([[0]], [1000000], 1)['scores'] == [1000000]


def test_exact_types():
    refuses(TypeError, TY, L([[0]]), [1], 1)
    refuses(TypeError, TY, T(([0],)), [1], 1)
    refuses(TypeError, TY, [[0]], L([1]), 1)
    refuses(TypeError, TY, [[0]], T((1,)), 1)
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [1], 1)
        refuses(TypeError, TY, [[0]], b, 1)
    refuses(ValueError, BL, [L([0])], [1], 1)
    refuses(ValueError, BL, [[0], T((0,))], [1, 1], 1)
    refuses(ValueError, BL, [[0], 'a'], [1, 1], 1)
    refuses(ValueError, BL, [[0], None], [1, 1], 1)
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, CC, [[0]], [1], b)
        refuses(ValueError, BI, [[b]], [1], 2)
        refuses(ValueError, BI, [[0], [1, b]], [1, 1], 2)
        refuses(ValueError, WT, [[0]], [b], 1)
        refuses(ValueError, WT, [[0], [0]], [1, b], 1)
    assert pv(((0, 1),), (1,), 2) == pv([[0, 1]], [1], 2)
    bal = [[0]]
    r = pv(bal, [1], 1)
    r['participant_contributions'][0].append(9)
    assert bal == [[0]]


def test_check_order():
    refuses(TypeError, TY, 1, 2, 3)
    refuses(ValueError, PC, [], [], True)
    refuses(ValueError, CC, [[True]], [True], True)
    refuses(ValueError, WC, [[True]], [True, 1], 1)
    refuses(ValueError, BL, [5], [True], 1)
    refuses(ValueError, BI, [[True]], [True], 1)
    refuses(ValueError, BU, [[0, 0]], [True], 2)
    refuses(ValueError, WT, [[0]], [True], 1)
