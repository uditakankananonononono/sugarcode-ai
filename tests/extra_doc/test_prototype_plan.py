"""Row 373 tests: oracle, caps at N and N+1, exact messages, exact-type and non-ASCII pins, check order."""
import pytest

from sugarcode.extra_doc.prototype_plan import plan_prototype as pp


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def refuses(error, msg, a):
    with pytest.raises(error) as e:
        pp(a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'tasks must be a list or tuple'
CNT = 'task count must be between 1 and 16'
TRI = 'tasks must be label days dependencies triples'
LAB = 'labels must be 1 to 40 characters without control or unassigned characters'
DAY = 'days must be nonbool integers 1 through 30'
DEPT = 'dependencies must be lists or tuples of at most eight indices'
DEPI = 'dependencies must be nonbool valid task indices'
DEPU = 'dependencies must be unique and not self-referencing'
UNI = 'labels must be unique'
CYC = 'dependencies contain a cycle'


def test_literals():
    r = pp([('a', 3, []), ('b', 2, [0]), ('c', 4, [0]), ('d', 1, [1, 2])])
    assert r == {'order': [0, 1, 2, 3], 'labels': ['a', 'b', 'c', 'd'], 'finish': [3, 5, 7, 8], 'total_days': 8,
                 'prototype_built': False}
    r = pp([('a', 1, [2]), ('b', 5, []), ('c', 2, [1])])                    # smallest ready index first
    assert r['order'] == [1, 2, 0] and r['finish'] == [8, 5, 7] and r['total_days'] == 8
    r = pp([('a', 4, []), ('b', 2, []), ('c', 3, [0, 1])])                  # parallel start, max over deps
    assert r['finish'] == [4, 2, 7] and r['order'] == [0, 1, 2]
    assert pp([('x', 30, [])])['total_days'] == 30
    assert pp((['a', 1, ()], ('b', 1, (0,))))['finish'] == [1, 2]
    assert pp([('a', 1, [1]), ('b', 1, []), ('c', 9, [])])['order'] == [1, 0, 2]


def test_caps_n_and_n_plus_1():
    assert pp([(str(i), 1, []) for i in range(16)])['total_days'] == 1
    refuses(ValueError, CNT, [(str(i), 1, []) for i in range(17)])
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [('a', 1)])
    refuses(ValueError, TRI, [('a', 1, [], 1)])
    assert pp([('a' * 40, 1, [])])['labels'] == ['a' * 40]
    refuses(ValueError, LAB, [('a' * 41, 1, [])])
    refuses(ValueError, LAB, [('a', 1, []), ('', 1, [])])
    assert pp([('a', 1, []), ('b', 30, [0])])['total_days'] == 31
    for d in (0, 31):
        refuses(ValueError, DAY, [('a', d, [])])
        refuses(ValueError, DAY, [('z', 1, []), ('a', d, [])])
    nine = [(str(i), 1, []) for i in range(9)]
    assert pp(nine + [('t', 1, list(range(8)))])['total_days'] == 2
    refuses(ValueError, DEPT, nine + [('t', 1, list(range(9)))])
    refuses(ValueError, DEPI, [('a', 1, [1])])
    refuses(ValueError, DEPI, [('a', 1, []), ('b', 1, [-1])])
    refuses(ValueError, DEPI, [('a', 1, []), ('b', 1, [2])])
    refuses(ValueError, DEPU, [('a', 1, [0])])
    refuses(ValueError, DEPU, [('a', 1, []), ('b', 1, [0, 0])])
    refuses(ValueError, UNI, [('a', 1, []), ('a', 1, [])])
    refuses(ValueError, CYC, [('a', 1, [1]), ('b', 1, [0])])
    refuses(ValueError, CYC, [('a', 1, []), ('b', 1, [2]), ('c', 1, [1])])


def test_non_ascii_witnesses():
    for ch in ('\x00', '\n', '\x7f', '\x85', '\u200b', '\ue000', '\ud800', '\u0378'):
        refuses(ValueError, LAB, [('a' + ch, 1, [])])
        refuses(ValueError, LAB, [(ch, 1, [])])
        refuses(ValueError, LAB, [('a', 1, []), ('b' + ch + 'c', 1, [])])
    assert pp([('caf\u00e9 \u4e2d \U0001f600', 1, [])])['labels'] == ['caf\u00e9 \u4e2d \U0001f600']


def test_exact_types():
    refuses(TypeError, TY, L([('a', 1, [])]))
    refuses(TypeError, TY, T((('a', 1, []),)))
    for x in (None, 'abc', {1}, {1: 1}, 5):
        refuses(TypeError, TY, x)
    refuses(ValueError, TRI, [L(['a', 1, []])])
    refuses(ValueError, TRI, [('a', 1, []), 'abc'])
    refuses(ValueError, TRI, [('a', 1, []), None])
    for x in (S('a'), 1, None, b'a'):
        refuses(ValueError, LAB, [(x, 1, [])])
        refuses(ValueError, LAB, [('a', 1, []), (x, 1, [])])
    for x in (True, False, 1.0, I(1), '1', None):
        refuses(ValueError, DAY, [('a', x, [])])
        refuses(ValueError, DAY, [('z', 1, []), ('a', x, [])])
    for x in (L(), None, 'a', {0}, 0):
        refuses(ValueError, DEPT, [('a', 1, x)])
        refuses(ValueError, DEPT, [('z', 1, []), ('a', 1, x)])
    for x in (True, False, 0.0, I(0), '0', None):
        refuses(ValueError, DEPI, [('a', 1, []), ('b', 1, [x])])
        refuses(ValueError, DEPI, [('a', 1, []), ('b', 1, [0, x])])
    src = [['a', 1, []]]
    r = pp(src)
    r['order'].append(7)
    assert src == [['a', 1, []]]


def test_check_order():
    refuses(TypeError, TY, 1)
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [5])
    refuses(ValueError, LAB, [('\n', True, 5)])
    refuses(ValueError, DAY, [('a', True, 5)])
    refuses(ValueError, DEPT, [('a', 1, 5)])
    refuses(ValueError, DEPI, [('a', 1, [True, 9])])
    refuses(ValueError, DEPU, [('a', 1, [0]), ('a', 1, [1])])
    refuses(ValueError, UNI, [('a', 1, []), ('a', 1, [0])])


def test_mixed_list_tuple_rows_both_orders():
    a, b = ('a', 1, []), ['b', 2, (0,)]
    assert pp([a, b]) == pp([list(a), list(b)]) == pp([tuple(a), tuple(b)])
    assert pp([['b', 2, ()], ('a', 1, [0])])['finish'] == [2, 3]
