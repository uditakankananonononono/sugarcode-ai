"""Row 367 tests: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import random
from fractions import Fraction as F

import pytest

from sugarcode.extra_doc.persona_development import build_persona as bp


class L(list):
    pass


class D(dict):
    pass


class S(str):
    pass


class I(int):
    pass


def refuses(error, msg, *a):
    with pytest.raises(error) as e:
        bp(*a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'records and attributes must be lists or tuples'
NR = 'record count must be between 1 and 40'
NA = 'attribute count must be between 1 and 4'
UA = 'attribute names must be unique'
RD = 'each record must be a dict'


def test_literals():
    rs = [{'a': 'x', 'b': 'p'}, {'a': 'y', 'b': 'p'}, {'a': 'y', 'b': 'q'}, {'a': 'x', 'b': 'q'}, {'a': 'y', 'b': 'p'}]
    assert bp(rs, ['a', 'b']) == {'persona': {'a': {'value': 'y', 'count': 3, 'share': F(3, 5)},
                                              'b': {'value': 'p', 'count': 3, 'share': F(3, 5)}},
                                  'record_count': 5, 'representative_validated': False}
    t = bp(rs[:4], ['a', 'b'])['persona']                                  # 2-2 ties: first appearance
    assert t['a']['value'] == 'x' and t['b']['value'] == 'p' and t['a']['share'] == F(1, 2)
    assert bp([{'a': 'x'}], ['a'])['persona']['a'] == {'value': 'x', 'count': 1, 'share': F(1)}
    assert bp([{'a': 'x'}, {'a': 'y'}, {'a': 'y'}], ['a'])['persona']['a']['value'] == 'y'
    assert bp(({'a': 'x', 'z': 'q'},), ('a',))['persona'] == {'a': {'value': 'x', 'count': 1, 'share': F(1)}}
    assert list(bp(rs, ['b', 'a'])['persona']) == ['b', 'a']


def test_random_oracle():
    rnd = random.Random(2)
    for _ in range(50):
        n = rnd.randint(1, 15)
        rs = [{'p': rnd.choice('abc'), 'q': rnd.choice('xy')} for _ in range(n)]
        out = bp(rs, ['p', 'q'])['persona']
        for k in 'pq':
            vals = [r[k] for r in rs]
            best = max(vals.count(v) for v in vals)
            first = next(v for v in vals if vals.count(v) == best)
            assert out[k] == {'value': first, 'count': best, 'share': F(best, n)}


def test_caps_n_and_n_plus_1():
    rs = [{'a': 'x'}] * 40
    assert bp(rs, ['a'])['record_count'] == 40
    refuses(ValueError, NR, rs + [{'a': 'x'}], ['a'])
    refuses(ValueError, NR, [], ['a'])
    r1 = [{k: 'v' for k in 'wxyz'}]
    assert bp(r1, list('wxyz'))['record_count'] == 1
    refuses(ValueError, NA, r1, list('wxyzq'))
    refuses(ValueError, NA, r1, [])
    assert bp([{'a' * 40: 'v' * 40}], ['a' * 40])['persona']['a' * 40]['value'] == 'v' * 40
    refuses(ValueError, 'attribute names must be 1 to 40 characters without control or unassigned characters', [{'a': 'v'}], ['a' * 41])
    refuses(ValueError, 'attribute names must be 1 to 40 characters without control or unassigned characters', [{'a': 'v'}], [''])
    refuses(ValueError, 'attribute values must be 1 to 40 characters without control or unassigned characters', [{'a': 'v' * 41}], ['a'])
    refuses(ValueError, 'attribute values must be 1 to 40 characters without control or unassigned characters', [{'a': ''}], ['a'])
    refuses(ValueError, 'attribute values must be 1 to 40 characters without control or unassigned characters', [{'a': 'v'}, {'a': ''}], ['a'])
    refuses(ValueError, UA, r1, ['w', 'w'])
    refuses(ValueError, 'record is missing attribute y', [{'x': 'v'}], ['x', 'y'])
    refuses(ValueError, 'record is missing attribute y', [{'x': 'v', 'y': 'v'}, {'x': 'v'}], ['x', 'y'])


def test_exact_types():
    r = [{'a': 'x'}]
    refuses(TypeError, TY, L(r), ['a'])
    refuses(TypeError, TY, r, L(['a']))
    for b in (None, 'a', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b, ['a'])
        refuses(TypeError, TY, r, b)
    refuses(TypeError, RD, [D(a='x')], ['a'])
    refuses(TypeError, RD, r + [[('a', 'x')]], ['a'])
    refuses(TypeError, RD, r + [None], ['a'])
    for b in (S('a'), 1, None, b'a'):
        refuses(TypeError, 'attribute names must be str', r, [b])
        refuses(TypeError, 'attribute names must be str', r, ['a', b])
        refuses(TypeError, 'attribute values must be str', [{'a': b}], ['a'])
        refuses(TypeError, 'attribute values must be str', r + [{'a': b}], ['a'])
        refuses(TypeError, 'attribute values must be str', [{'a': 'x', 'b': b}], ['a', 'b'])
    src = [{'a': 'x'}]
    out = bp(src, ['a'])
    out['persona']['a']['value'] = 'z'
    assert src == [{'a': 'x'}]


def test_check_order():
    refuses(TypeError, TY, 1, 2)
    refuses(ValueError, NR, [], [], )
    refuses(ValueError, NA, [5], [])
    refuses(TypeError, 'attribute names must be str', [5], [5])
    refuses(ValueError, UA, [5], ['a', 'a'])
    refuses(TypeError, RD, [5], ['a'])
    refuses(ValueError, 'record is missing attribute a', [{}], ['a'])
    refuses(TypeError, 'attribute values must be str', [{'a': 1}], ['a'])


def test_non_ascii_witnesses():
    for ch in ('\x00', '\n', '\x7f', '\x85', '\u200b', '\ue000', '\ud800', '\u0378'):
        refuses(ValueError, 'attribute names must be 1 to 40 characters without control or unassigned characters', [{'a': 'v'}], ['a' + ch])
        refuses(ValueError, 'attribute values must be 1 to 40 characters without control or unassigned characters', [{'a': 'v' + ch}], ['a'])
        refuses(ValueError, 'attribute values must be 1 to 40 characters without control or unassigned characters', [{'a': 'v'}, {'a': ch}], ['a'])
    assert bp([{'a': 'caf\u00e9 \u4e2d \U0001f600'}], ['a'])['persona']['a']['value'] == 'caf\u00e9 \u4e2d \U0001f600'
