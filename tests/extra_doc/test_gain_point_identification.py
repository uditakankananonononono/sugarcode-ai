"""Row 370 tests: oracle, caps at N and N+1, exact messages, exact-type pins, check order."""
import pytest

from sugarcode.extra_doc.gain_point_identification import rank_gains as rg


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
        rg(a)
    assert type(e.value) is error and str(e.value) == msg


TY = 'outcomes must be a list or tuple'
CNT = 'outcome count must be between 1 and 32'
TRI = 'outcomes must be label importance delivery triples'
LAB = 'labels must be strings of length 1 through 40 without control or unassigned characters'
RAT = 'ratings must be nonbool integers zero through 100'
UNI = 'labels must be unique'


def test_literals_and_oracle():
    r = rg([('a', 10, 0), ('b', 5, 50), ('c', 100, 0), ('d', 0, 0), ('e', 50, 100)])
    assert r == {'ranked': [{'label': 'c', 'opportunity': 10000}, {'label': 'a', 'opportunity': 1000},
                            {'label': 'b', 'opportunity': 250}], 'zero_opportunity': ['d', 'e'],
                 'outcomes_validated': False}
    assert [x['label'] for x in rg([('x', 1, 50), ('a', 1, 0), ('b', 1, 50)])['ranked']] == ['a', 'x', 'b']  # tie: index
    assert rg([('a', 1, 99)])['ranked'][0]['opportunity'] == 1 and rg([('a', 1, 100)])['ranked'] == []
    assert rg((['a', 3, 4],))['ranked'][0]['opportunity'] == 288
    assert rg([('a', 100, 0)])['ranked'][0]['opportunity'] == 10000


def test_caps_n_and_n_plus_1():
    assert len(rg([(str(i), 1, 0) for i in range(32)])['ranked']) == 32
    refuses(ValueError, CNT, [(str(i), 1, 0) for i in range(33)])
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [('a', 1)])
    refuses(ValueError, TRI, [('a', 1, 0), ('b', 1, 0, 0)])
    assert rg([('a' * 40, 1, 0)])['ranked'][0]['label'] == 'a' * 40
    refuses(ValueError, LAB, [('a' * 41, 1, 0)])
    refuses(ValueError, LAB, [('a', 1, 0), ('', 1, 0)])
    for b in (-1, 101):
        for pos in (1, 2):
            row = ['a', 1, 1]
            row[pos] = b
            refuses(ValueError, RAT, [row])
            refuses(ValueError, RAT, [('z', 1, 1), row])
    refuses(ValueError, UNI, [('a', 1, 0), ('a', 2, 0)])


def test_exact_types():
    refuses(TypeError, TY, L([('a', 1, 0)]))
    refuses(TypeError, TY, T((('a', 1, 0),)))
    for b in (None, 'abc', {1}, {1: 1}, 5):
        refuses(TypeError, TY, b)
    refuses(ValueError, TRI, [L(['a', 1, 0])])
    refuses(ValueError, TRI, [('a', 1, 0), 'bcd'])
    refuses(ValueError, TRI, [('a', 1, 0), None])
    for b in (S('a'), 1, None, b'a'):
        refuses(ValueError, LAB, [(b, 1, 0)])
        refuses(ValueError, LAB, [('a', 1, 0), (b, 1, 0)])
    for b in (True, False, 1.0, I(1), '1', None):
        for pos in (1, 2):
            row = ['a', 1, 1]
            row[pos] = b
            refuses(ValueError, RAT, [row])
            refuses(ValueError, RAT, [('z', 1, 1), row])
    src = [['a', 1, 0]]
    r = rg(src)
    r['ranked'].append(1)
    assert src == [['a', 1, 0]]


def test_check_order():
    refuses(TypeError, TY, 1)
    refuses(ValueError, CNT, [])
    refuses(ValueError, TRI, [5])
    refuses(ValueError, LAB, [(1, True, 0)])
    refuses(ValueError, RAT, [('a', True, 0), ('a', 1, 1)])


def test_non_ascii_witnesses():
    for ch in ('\x00', '\n', '\x7f', '\x85', '\u200b', '\ue000', '\ud800', '\u0378'):
        refuses(ValueError, LAB, [('a' + ch, 1, 0)])
        refuses(ValueError, LAB, [(ch, 1, 0)])
        refuses(ValueError, LAB, [('a', 1, 0), ('b' + ch + 'c', 1, 0)])
    assert rg([('caf\u00e9 \u4e2d \U0001f600', 1, 0)])['ranked'][0]['label'] == 'caf\u00e9 \u4e2d \U0001f600'
