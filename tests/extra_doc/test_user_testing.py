"""Row 374 tests: oracle, caps at N and N+1, exact messages, exact-type and non-ASCII pins, check order."""
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc.user_testing import OUTCOMES, tally_sessions as ts


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


def refuses(error, msg, a):
    with pytest.raises(error) as e:
        ts(a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'observations must be a list or tuple'
CNT = 'observation count must be between 1 and 64'
TRI = 'observations must be participant task outcome triples'
TXT = 'participants and tasks must be 1 to 40 characters without control or unassigned characters'
OUT = 'outcome must be pass, assist or fail'
DUP = 'each participant may appear once per task'


def test_names():
    assert OUTCOMES == ('pass', 'assist', 'fail')


def test_literals():
    r = ts([('p1', 'login', 'pass'), ('p2', 'login', 'fail'), ('p1', 'pay', 'pass'), ('p2', 'pay', 'pass'),
            ('p3', 'login', 'assist')])
    assert r['tasks'] == [{'task': 'login', 'pass': 1, 'assist': 1, 'fail': 1, 'observations': 3, 'pass_rate': F(1, 3)},
                          {'task': 'pay', 'pass': 2, 'assist': 0, 'fail': 0, 'observations': 2, 'pass_rate': F(1)}]
    assert r['weak_tasks'] == ['login'] and r['sessions_validated'] is False
    r = ts([('p', 'a', 'pass'), ('p', 'b', 'fail'), ('p', 'c', 'assist'), ('q', 'c', 'pass'), ('q', 'a', 'fail'), ('q', 'b', 'fail')])
    assert [x['task'] for x in r['tasks']] == ['a', 'b', 'c']
    assert r['weak_tasks'] == ['b', 'a', 'c']                                 # 0, 1/2 then 1/2 by appearance
    r = ts([('p', 'a', 'assist'), ('p', 'b', 'fail')])
    assert r['weak_tasks'] == ['a', 'b']                                      # both 0: appearance order
    assert ts([('p', 'a', 'pass')])['weak_tasks'] == []
    assert ts((['p', 'a', 'pass'],))['tasks'][0]['pass_rate'] == 1
    assert ts([('p', 'a', 'fail'), ('q', 'a', 'pass'), ('r', 'a', 'pass')])['tasks'][0]['pass_rate'] == F(2, 3)


def test_caps_n_and_n_plus_1():
    assert ts([('p%d' % i, 't', 'pass') for i in range(64)])['tasks'][0]['observations'] == 64
    refuses(ValueError, CNT, [('p%d' % i, 't', 'pass') for i in range(65)])
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [('p', 't')])
    refuses(ValueError, TRI, [('p', 't', 'pass', 1)])
    assert ts([('p' * 40, 't' * 40, 'pass')])['tasks'][0]['task'] == 't' * 40
    for i in (0, 1):
        row = ['p', 't', 'pass']
        row[i] = 'x' * 41
        refuses(ValueError, TXT, [row])
        refuses(ValueError, TXT, [('q', 'u', 'pass'), row])
        row[i] = ''
        refuses(ValueError, TXT, [row])
    for o in ('Pass', 'pass ', '', 'x'):
        refuses(ValueError, OUT, [('p', 't', o)])
        refuses(ValueError, OUT, [('q', 'u', 'pass'), ('p', 't', o)])
    refuses(ValueError, DUP, [('p', 't', 'pass'), ('p', 't', 'fail')])
    assert len(ts([('p', 't', 'pass'), ('p', 'u', 'pass'), ('q', 't', 'pass')])['tasks']) == 2


def test_non_ascii_witnesses():
    for ch in ('\x00', '\n', '\x7f', '\x85', '\u200b', '\ue000', '\ud800', '\u0378'):
        for i in (0, 1):
            row = ['p', 't', 'pass']
            row[i] = 'a' + ch
            refuses(ValueError, TXT, [row])
            row[i] = ch
            refuses(ValueError, TXT, [row])
            refuses(ValueError, TXT, [('q', 'u', 'pass'), ['b' + ch + 'c' if j == i else 'z' for j in (0, 1)] + ['pass']])
    assert ts([('caf\u00e9', '\u4e2d \U0001f600', 'pass')])['tasks'][0]['task'] == '\u4e2d \U0001f600'


def test_exact_types():
    refuses(TypeError, TY, L([('p', 't', 'pass')]))
    refuses(TypeError, TY, T((('p', 't', 'pass'),)))
    for b in (None, 'abc', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b)
    refuses(ValueError, TRI, [L(['p', 't', 'pass'])])
    refuses(ValueError, TRI, [('p', 't', 'pass'), 'abc'])
    refuses(ValueError, TRI, [('p', 't', 'pass'), None])
    for b in (S('a'), 1, None, b'a', True):
        for i in (0, 1):
            row = ['p', 't', 'pass']
            row[i] = b
            refuses(ValueError, TXT, [row])
            refuses(ValueError, TXT, [('q', 'u', 'pass'), row])
        refuses(ValueError, OUT, [('p', 't', b)])
    refuses(ValueError, OUT, [('p', 't', S('pass'))])
    src = [['p', 't', 'pass']]
    r = ts(src)
    r['tasks'].append(1)
    assert src == [['p', 't', 'pass']]


def test_mixed_rows_both_orders():
    a, b = ('p', 't', 'pass'), ['q', 't', 'fail']
    assert ts([a, b]) == ts([tuple(a), tuple(b)]) == ts([list(a), list(b)])
    assert ts([b, a])['tasks'][0]['pass_rate'] == F(1, 2)


def test_check_order():
    refuses(TypeError, TY, 1)
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [5])
    refuses(ValueError, TXT, [('\n', 't', 'bad')])
    refuses(ValueError, OUT, [('p', 't', 'bad'), ('p', 't', 'bad')])
