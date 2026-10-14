"""Row 366 tests-only hardening: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc.customer_segments import NOT_CLAIMED, identify_segments as seg


class L(list):
    pass


class T(tuple):
    pass


class D(dict):
    pass


class S(str):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        seg(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'customers and attributes must be lists or tuples'
NC = 'customer count must be between 1 and 40'
NA = 'attribute count must be between 1 and 4'
MT = 'min_size must be nonbool int'
MR = 'min_size must be between 1 and 40'
UA = 'attribute names must be unique'
PAIR = 'each customer must be (id, attributes)'
DT = 'customer attributes must be a dict'
CU = 'customer ids must be unique'


def test_not_claimed():
    assert NOT_CLAIMED == ('records are accurate, lawful or representative', 'market size', 'target-market choice',
                           'demand', 'willingness to pay', 'behavioral differences between segments',
                           'legal or approval-gate clearance', 'deployment')


def test_literals_and_oracle():
    cs = [('a', {'x': '1', 'y': 'p'}), ('b', {'x': '2', 'y': 'p'}), ('c', {'x': '1', 'y': 'p'}), ('d', {'x': '2', 'y': 'q'})]
    r = seg(cs, ['x', 'y'], 2)
    assert r['segments'] == [
        {'attributes': {'x': '1', 'y': 'p'}, 'members': ['a', 'c'], 'size': 2, 'share': F(1, 2), 'qualifying': True},
        {'attributes': {'x': '2', 'y': 'p'}, 'members': ['b'], 'size': 1, 'share': F(1, 4), 'qualifying': False},
        {'attributes': {'x': '2', 'y': 'q'}, 'members': ['d'], 'size': 1, 'share': F(1, 4), 'qualifying': False}]
    assert (r['segment_count'], r['qualifying_count'], r['qualifying_share'], r['customer_count']) == (3, 1, F(1, 2), 4)
    assert r['target_market_validated'] is False and r['not_claimed'] is NOT_CLAIMED
    r = seg(cs, ['y'])                                                   # default min_size 1
    assert r['qualifying_count'] == 2 and r['qualifying_share'] == 1
    assert [s['members'] for s in seg(cs, ['y'])['segments']] == [['a', 'b', 'c'], ['d']]
    r = seg(cs, ['x'], 3)                                                # ties: first appearance
    assert [s['members'] for s in r['segments']] == [['a', 'c'], ['b', 'd']] and r['qualifying_count'] == 0
    assert r['qualifying_share'] == 0
    assert seg(cs, ['y', 'x'])['segments'][0]['attributes'] == {'y': 'p', 'x': '1'}
    assert seg(tuple(cs), ('x',))['segment_count'] == 2
    assert seg([('a', {'x': '1', 'z': 'ignored'})], ['x'])['segments'][0]['attributes'] == {'x': '1'}
    assert seg([('a', {'x': '1'}), ('b', {'x': '2'}), ('c', {'x': '2'})], ['x'])['segments'][0]['members'] == ['b', 'c']


def test_random_oracle():
    rnd = random.Random(3)
    for _ in range(40):
        n = rnd.randint(1, 12)
        cs = [('c%d' % i, {'p': rnd.choice('ab'), 'q': rnd.choice('xyz')}) for i in range(n)]
        ms = rnd.randint(1, 5)
        r = seg(cs, ['p', 'q'], ms)
        g = {}
        for cid, a in cs:
            g.setdefault((a['p'], a['q']), []).append(cid)
        exp = sorted(g.items(), key=lambda kv: -len(kv[1]))              # stable: first appearance on ties
        assert [s['members'] for s in r['segments']] == [m for _, m in exp]
        assert [s['qualifying'] for s in r['segments']] == [len(m) >= ms for _, m in exp]
        assert r['qualifying_share'] == F(sum(len(m) for _, m in exp if len(m) >= ms), n)
        assert sum(s['share'] for s in r['segments']) == 1


def test_caps_n_and_n_plus_1():
    ok = [(str(i), {'x': '1'}) for i in range(40)]
    assert seg(ok, ['x'], 40)['qualifying_count'] == 1
    refuses(ValueError, NC, ok + [('z', {'x': '1'})], ['x'])
    refuses(ValueError, NC, [], ['x'])
    c1 = [('a', {k: 'v' for k in 'wxyz'})]
    assert seg(c1, list('wxyz'))['segment_count'] == 1
    refuses(ValueError, NA, c1, list('wxyzq'))
    refuses(ValueError, NA, c1, [])
    refuses(ValueError, MR, c1, ['w'], 0)
    refuses(ValueError, MR, c1, ['w'], 41)
    assert seg(c1, ['w'], 1)['qualifying_count'] == 1
    assert seg([('i' * 40, {'a' * 40: 'v' * 40})], ['a' * 40])['segments'][0]['members'] == ['i' * 40]
    refuses(ValueError, 'customer ids must be 1 to 40 characters', [('i' * 41, {'x': 'v'})], ['x'])
    refuses(ValueError, 'customer ids must be 1 to 40 characters', [('', {'x': 'v'})], ['x'])
    refuses(ValueError, 'attribute names must be 1 to 40 characters', c1, ['a' * 41])
    refuses(ValueError, 'attribute names must be 1 to 40 characters', c1, [''])
    refuses(ValueError, 'attribute values must be 1 to 40 characters', [('a', {'x': 'v' * 41})], ['x'])
    refuses(ValueError, 'attribute values must be 1 to 40 characters', [('a', {'x': ''})], ['x'])
    refuses(ValueError, 'attribute values must be 1 to 40 characters', [('a', {'x': 'v'}), ('b', {'x': ''})], ['x'])
    refuses(ValueError, UA, c1, ['w', 'w'])
    refuses(ValueError, CU, [('a', {'x': '1'}), ('a', {'x': '2'})], ['x'])
    refuses(ValueError, 'customer is missing attribute y', [('a', {'x': '1'})], ['x', 'y'])
    refuses(ValueError, 'customer is missing attribute y', [('a', {'x': '1', 'y': '1'}), ('b', {'x': '1'})], ['x', 'y'])
    refuses(ValueError, 'customer is missing attribute y', [('a', {'z': '1'})], ['y', 'x'])


def test_exact_types():
    c = [('a', {'x': '1'})]
    refuses(TypeError, TY, L(c), ['x'])
    refuses(TypeError, TY, c, L(['x']))
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, ['x'])
        refuses(TypeError, TY, c, b)
    for b in (True, False, 1.0, I(1), '1', None):
        refuses(TypeError, MT, c, ['x'], b)
    refuses(ValueError, PAIR, [L(['a', {'x': '1'}])], ['x'])
    refuses(ValueError, PAIR, c + [('b',)], ['x'])
    refuses(ValueError, PAIR, c + ['ab'], ['x'])
    refuses(ValueError, PAIR, c + [None], ['x'])
    refuses(TypeError, DT, [('a', D(x='1'))], ['x'])
    refuses(TypeError, DT, c + [('b', [('x', '1')])], ['x'])
    refuses(TypeError, DT, c + [('b', None)], ['x'])
    for b in (S('a'), 1, None, b'a'):
        refuses(TypeError, 'customer ids must be str', [(b, {'x': '1'})], ['x'])
        refuses(TypeError, 'customer ids must be str', c + [(b, {'x': '1'})], ['x'])
        refuses(TypeError, 'attribute names must be str', c, [b])
        refuses(TypeError, 'attribute names must be str', c, ['x', b])
        refuses(TypeError, 'attribute values must be str', [('a', {'x': b})], ['x'])
        refuses(TypeError, 'attribute values must be str', [('a', {'x': '1', 'y': b})], ['x', 'y'])
        refuses(TypeError, 'attribute values must be str', c + [('b', {'x': b})], ['x'])
    assert seg([['a', {'x': '1'}]], ['x'])['customer_count'] == 1
    src = {'x': '1'}
    r = seg([('a', src)], ['x'])
    r['segments'][0]['attributes']['x'] = 'z'
    assert src == {'x': '1'}


def test_check_order():
    refuses(TypeError, TY, 1, 2)
    refuses(ValueError, NC, [], [], 'a')
    refuses(ValueError, NA, [('a', {})], [], 'a')
    refuses(TypeError, MT, [('a', {})], ['x'], True)
    refuses(ValueError, MR, [('a', {})], [5], 0)
    refuses(TypeError, 'attribute names must be str', [('a', {})], [5])
    refuses(ValueError, UA, [5], ['x', 'x'])
    refuses(ValueError, PAIR, [5], ['x'])
    refuses(TypeError, DT, [('a', 5)], ['x'])
    refuses(TypeError, 'customer ids must be str', [(5, {})], ['x'])
    refuses(ValueError, 'customer is missing attribute x', [('a', {})], ['x'])
    refuses(ValueError, CU, [('a', {'x': '1'}), ('a', {'x': '1'})], ['x'])
