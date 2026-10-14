"""Row 371 tests: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import pytest

from sugarcode.extra_doc.jobs_to_be_done import analyze_jobs as aj


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


def refuses(error, msg, a):
    with pytest.raises(error) as e:
        aj(a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'jobs must be a list or tuple'
CNT = 'job count must be between 1 and 24'
TRI = 'jobs must be situation motivation outcome triples'
TXT = 'job text must be strings of length 1 through 80 without control or unassigned characters'


def test_literals_and_oracle():
    r = aj([('s1', 'm1', 'o1'), ('s2', 'm2', 'o2'), ('s3', 'm2', 'o3'), ('s4', 'm1', 'o4'), ('s5', 'm3', 'o5')])
    assert r == {'statements': ['When s1, I want to m1, so I can o1', 'When s2, I want to m2, so I can o2',
                                'When s3, I want to m2, so I can o3', 'When s4, I want to m1, so I can o4',
                                'When s5, I want to m3, so I can o5'],
                 'motivations': [{'motivation': 'm1', 'count': 2}, {'motivation': 'm2', 'count': 2},
                                 {'motivation': 'm3', 'count': 1}], 'motivation_validated': False}
    assert [m['motivation'] for m in aj([('a', 'x', 'b'), ('a', 'y', 'b'), ('a', 'y', 'b')])['motivations']] == ['y', 'x']
    assert aj((['a', 'b', 'c'],))['statements'] == ['When a, I want to b, so I can c']


def test_caps_n_and_n_plus_1():
    assert len(aj([('a', str(i), 'c') for i in range(24)])['statements']) == 24
    refuses(ValueError, CNT, [('a', 'b', 'c')] * 25)
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [('a', 'b')])
    refuses(ValueError, TRI, [('a', 'b', 'c'), ('a', 'b', 'c', 'd')])
    for pos in range(3):
        row = ['a', 'b', 'c']
        row[pos] = 'x' * 80
        assert aj([row])['statements']
        row[pos] = 'x' * 81
        refuses(ValueError, TXT, [row])
        refuses(ValueError, TXT, [('a', 'b', 'c'), row])
        row[pos] = ''
        refuses(ValueError, TXT, [row])


def test_exact_types():
    refuses(TypeError, TY, L([('a', 'b', 'c')]))
    refuses(TypeError, TY, L())
    for b in (None, 'abc', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b)
    refuses(ValueError, TRI, [L(['a', 'b', 'c'])])
    refuses(ValueError, TRI, [('a', 'b', 'c'), 'abc'])
    refuses(ValueError, TRI, [('a', 'b', 'c'), None])
    for b in (S('a'), 1, None, b'a', True):
        for pos in range(3):
            row = ['a', 'b', 'c']
            row[pos] = b
            refuses(ValueError, TXT, [row])
            refuses(ValueError, TXT, [('a', 'b', 'c'), row])
    src = [['a', 'b', 'c']]
    r = aj(src)
    r['statements'].append('x')
    assert src == [['a', 'b', 'c']]


def test_check_order():
    refuses(TypeError, TY, 1)
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [5])
    refuses(ValueError, TXT, [(1, 2, 3)])


def test_non_ascii_witnesses():
    for ch in ('\x00', '\n', '\x7f', '\x85', '\u200b', '\ue000', '\ud800', '\u0378'):
        for pos in range(3):
            row = ['a', 'b', 'c']
            row[pos] = 'x' + ch
            refuses(ValueError, TXT, [row])
            refuses(ValueError, TXT, [('a', 'b', 'c'), row])
    assert aj([('caf\u00e9', '\u4e2d', '\U0001f600')])['statements']


def test_mixed_list_tuple_rows_both_orders():
    a, b = ('s', 'm', 'o'), ['s', 'n', 'p']
    assert aj([a, b]) == aj([list(a), list(b)]) == aj([tuple(a), tuple(b)])
    assert [m['motivation'] for m in aj([b, a])['motivations']] == ['n', 'm']
    assert [m['motivation'] for m in aj([a, b])['motivations']] == ['m', 'n']
