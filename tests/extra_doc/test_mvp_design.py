"""Row 372 tests: oracle, caps at N and N+1, exact messages, exact-type and non-ASCII pins, check order."""
import itertools

import pytest

from sugarcode.extra_doc.mvp_design import select_tests as st


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def refuses(error, msg, a, b=10):
    with pytest.raises(error) as e:
        st(a, b)
    assert type(e.value) is error and str(e.value) == msg


TY = 'hypotheses must be a list or tuple'
CNT = 'hypothesis count must be between 1 and 12'
TRI = 'hypotheses must be label cost learning triples'
LAB = 'labels must be 1 to 40 characters without control or unassigned characters'
VAL = 'cost and learning must be nonbool integers zero through 1000'
BUD = 'budget must be a nonbool integer zero through 10000'
UNI = 'labels must be unique'


def oracle(h, b):
    best = None
    for r in range(len(h) + 1):
        for ch in itertools.combinations(range(len(h)), r):
            c = sum(h[i][1] for i in ch)
            if c <= b:
                k = (-sum(h[i][2] for i in ch), c, r, ch)
                if best is None or k < best:
                    best = k
    return best


CASES = [([('a', 3, 5), ('b', 2, 4), ('c', 4, 3)], 5), ([('a', 3, 5), ('b', 2, 4), ('c', 4, 3)], 9),
         ([('a', 1, 1), ('b', 1, 1)], 2), ([('a', 1, 1), ('b', 1, 1)], 1), ([('a', 2, 3), ('b', 1, 3)], 2),
         ([('a', 0, 0), ('b', 0, 0)], 0), ([('a', 5, 9)], 4), ([('a', 1, 2), ('b', 1, 1), ('c', 2, 3)], 2)]


@pytest.mark.parametrize('h,b', CASES)
def test_oracle(h, b):
    k = oracle(h, b)
    r = st(h, b)
    assert r['selected'] == list(k[3]) and r['learning'] == -k[0] and r['cost'] == k[1]
    assert r['labels'] == [h[i][0] for i in k[3]] and r['hypotheses_tested'] is False


def test_literals():
    assert st([('a', 2, 3), ('b', 1, 3)], 2)['selected'] == [1]
    assert st([('a', 1, 1), ('b', 1, 1)], 1)['selected'] == [0]
    assert st([('a', 0, 0), ('b', 0, 0)], 0)['selected'] == []
    assert st((['a', 1, 1],), 1)['selected'] == [0]
    assert st([('a', 5, 9)], 5)['selected'] == [0] and st([('a', 5, 9)], 4)['selected'] == []


def test_caps_n_and_n_plus_1():
    assert st([(str(i), 0, 1) for i in range(12)], 0)['learning'] == 12
    refuses(ValueError, CNT, [(str(i), 0, 1) for i in range(13)])
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [('a', 1)])
    refuses(ValueError, TRI, [('a', 1, 1, 1)])
    assert st([('a' * 40, 1, 1)], 10)['labels'] == ['a' * 40]
    refuses(ValueError, LAB, [('a' * 41, 1, 1)])
    refuses(ValueError, LAB, [('a', 1, 1), ('', 1, 1)])
    for pos in (1, 2):
        row = ['a', 1, 1]
        row[pos] = 1000
        assert st([row], 10000)['cost' if pos == 1 else 'learning'] == 1000
        for b in (-1, 1001):
            row[pos] = b
            refuses(ValueError, VAL, [row])
            refuses(ValueError, VAL, [('z', 1, 1), row])
    assert st([('a', 1, 1)], 10000)['cost'] == 1
    assert st([('a', 1, 1)], 0)['cost'] == 0
    refuses(ValueError, BUD, [('a', 1, 1)], -1)
    refuses(ValueError, BUD, [('a', 1, 1)], 10001)
    refuses(ValueError, UNI, [('a', 1, 1), ('a', 2, 2)])


def test_non_ascii_witnesses():
    for ch in ('\x00', '\n', '\x7f', '\x85', '\u200b', '\ue000', '\ud800', '\u0378'):
        refuses(ValueError, LAB, [('a' + ch, 1, 1)])
        refuses(ValueError, LAB, [(ch, 1, 1)])
        refuses(ValueError, LAB, [('a', 1, 1), ('b' + ch + 'c', 1, 1)])
    assert st([('caf\u00e9 \u4e2d \U0001f600', 1, 1)], 1)['labels'] == ['caf\u00e9 \u4e2d \U0001f600']
    assert st([('a b', 1, 1)], 1)['selected'] == [0]


def test_exact_types():
    refuses(TypeError, TY, L([('a', 1, 1)]))
    refuses(TypeError, TY, T((('a', 1, 1),)))
    for x in (None, 'abc', {1}, {1: 1}, 5):
        refuses(TypeError, TY, x)
    refuses(ValueError, TRI, [L(['a', 1, 1])])
    refuses(ValueError, TRI, [('a', 1, 1), 'abc'])
    refuses(ValueError, TRI, [('a', 1, 1), None])
    for x in (S('a'), 1, None, b'a'):
        refuses(ValueError, LAB, [(x, 1, 1)])
        refuses(ValueError, LAB, [('a', 1, 1), (x, 1, 1)])
    for x in (True, False, 1.0, I(1), '1', None):
        for pos in (1, 2):
            row = ['a', 1, 1]
            row[pos] = x
            refuses(ValueError, VAL, [row])
            refuses(ValueError, VAL, [('z', 1, 1), row])
        refuses(ValueError, BUD, [('a', 1, 1)], x)
    src = [['a', 1, 1]]
    r = st(src, 5)
    r['selected'].append(9)
    assert src == [['a', 1, 1]]


def test_check_order():
    refuses(TypeError, TY, 1, 'x')
    refuses(ValueError, CNT, [], 'x')
    refuses(ValueError, TRI, [5], 'x')
    refuses(ValueError, LAB, [('\n', True, 1)], 'x')
    refuses(ValueError, VAL, [('a', True, 1), ('a', 1, 1)], 'x')
    refuses(ValueError, BUD, [('a', 1, 1), ('a', 1, 1)], 'x')


def test_mixed_list_tuple_rows_both_orders():
    a, b = ('a', 1, 1), ['b', 2, 2]
    assert st([a, b], 5) == st([list(a), list(b)], 5) == st([tuple(a), tuple(b)], 5)
    assert st([b, a], 5)['labels'] == ['b', 'a'] and st([a, b], 5)['labels'] == ['a', 'b']
