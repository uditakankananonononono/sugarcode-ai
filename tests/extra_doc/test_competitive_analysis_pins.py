"""Row 361 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import pytest

from sugarcode.extra_doc.competitive_analysis import competitive_map as cm


class L(list):
    pass


class T(tuple):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        cm(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'inputs must be lists or tuples'
CNT = 'competitor and criterion counts must be between 1 and 16'
SHP = 'criterion shapes must agree'
VAL = 'scores and weights must be nonbool integers zero through 1000'
WZ = 'at least one weight must be positive'


def oracle(scores, base, w):
    rows = []
    for row in scores:
        d = [row[j] - base[j] for j in range(len(base))]
        rows.append({'strengths': [j for j in range(len(d)) if d[j] > 0], 'weaknesses': [j for j in range(len(d)) if d[j] < 0],
                     'parity': [j for j in range(len(d)) if d[j] == 0], 'weighted_delta': sum(d[j] * w[j] for j in range(len(d)))})
    order = sorted(range(len(rows)), key=lambda i: (-rows[i]['weighted_delta'], i))
    return rows, order


CASES = [
    ([[5, 1], [3, 3], [4, 2]], [3, 3], [2, 1]),
    ([[3, 3], [3, 3]], [3, 3], [1, 1]),
    ([[0, 1000], [1000, 0]], [500, 500], [1, 1]),
    ([[1, 2, 3]], [3, 2, 1], [0, 5, 0]),
    ([[4], [4], [2]], [3], [7]),
    ([[1, 0], [0, 1]], [0, 0], [1, 2]),
]


@pytest.mark.parametrize('s,b,w', CASES)
def test_oracle(s, b, w):
    rows, order = oracle(s, b, w)
    assert cm(s, b, w) == {'competitors': rows, 'ranking': order, 'scores_verified': False}


def test_literals_and_tie_order():
    r = cm([[5, 1], [3, 3], [4, 2]], [3, 3], [2, 1])
    assert r['competitors'][0] == {'strengths': [0], 'weaknesses': [1], 'parity': [], 'weighted_delta': 2}
    assert r['competitors'][1] == {'strengths': [], 'weaknesses': [], 'parity': [0, 1], 'weighted_delta': 0}
    assert r['ranking'] == [0, 2, 1]
    assert cm([[3], [3], [3]], [3], [1])['ranking'] == [0, 1, 2]                  # ties: lower index first
    assert cm([[1], [9]], [5], [1])['ranking'] == [1, 0]
    assert cm([[5], [5]], [3], [1])['competitors'][0]['weighted_delta'] == 2
    assert cm([[2, 2]], [0, 0], [1000, 1000])['competitors'][0]['weighted_delta'] == 4000


def test_caps_and_bounds_n_and_n_plus_1():
    assert cm([[1]] * 16, [1], [1])['ranking'] == list(range(16))
    refuses(ValueError, CNT, [[1]] * 17, [1], [1])
    refuses(ValueError, CNT, [], [1], [1])
    assert len(cm([[1] * 16], [1] * 16, [1] * 16)['competitors'][0]['parity']) == 16
    refuses(ValueError, CNT, [[1] * 17], [1] * 17, [1] * 17)
    refuses(ValueError, CNT, [[]], [], [])
    refuses(ValueError, SHP, [[1, 1]], [1, 1], [1])
    refuses(ValueError, SHP, [[1, 1]], [1, 1], [1, 1, 1])
    refuses(ValueError, SHP, [[1]], [1, 1], [1, 1])
    refuses(ValueError, SHP, [[1, 1], [1]], [1, 1], [1, 1])
    refuses(ValueError, SHP, [[1, 1], [1, 1, 1]], [1, 1], [1, 1])
    for b in (-1, 1001):
        refuses(ValueError, VAL, [[1]], [b], [1])
        refuses(ValueError, VAL, [[1]], [1], [b])
        refuses(ValueError, VAL, [[b]], [1], [1])
        refuses(ValueError, VAL, [[1], [b]], [1], [1])
        refuses(ValueError, VAL, [[1, 1], [1, b]], [1, 1], [1, 1])
    assert cm([[1000]], [0], [1000])['competitors'][0]['weighted_delta'] == 1000000
    refuses(ValueError, WZ, [[1]], [1], [0])
    refuses(ValueError, WZ, [[1, 1]], [1, 1], [0, 0])
    assert cm([[1, 1]], [1, 1], [0, 1])['ranking'] == [0]


def test_exact_types():
    refuses(TypeError, TY, L([[1]]), [1], [1])
    refuses(TypeError, TY, T(([1],)), [1], [1])
    refuses(TypeError, TY, [[1]], L([1]), [1])
    refuses(TypeError, TY, [[1]], [1], L([1]))
    refuses(TypeError, TY, [[1]], T((1,)), [1])
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, [1], [1])
        refuses(TypeError, TY, [[1]], b, [1])
        refuses(TypeError, TY, [[1]], [1], b)
    refuses(ValueError, SHP, [L([1])], [1], [1])
    refuses(ValueError, SHP, [[1], T((1,))], [1], [1])
    refuses(ValueError, SHP, [[1], 'a'], [1], [1])
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, VAL, [[1]], [b], [1])
        refuses(ValueError, VAL, [[1]], [1], [b])
        refuses(ValueError, VAL, [[b]], [1], [1])
        refuses(ValueError, VAL, [[1], [b]], [1], [1])
        refuses(ValueError, VAL, [[1, 1], [1, b]], [1, 1], [1, 1])
    assert cm(((1,),), (1,), (1,)) == cm([[1]], [1], [1])
    s = [[1]]
    r = cm(s, [1], [1])
    r['competitors'][0]['parity'].append(9)
    assert s == [[1]]


def test_check_order():
    refuses(TypeError, TY, 1, 2, 3)
    refuses(ValueError, CNT, [], [], [])
    refuses(ValueError, SHP, [[True]], [True], [True, 1])
    refuses(ValueError, VAL, [[1]], [True], [0])
    refuses(ValueError, VAL, [[True]], [1], [0])
    refuses(ValueError, WZ, [[1]], [1], [0])
