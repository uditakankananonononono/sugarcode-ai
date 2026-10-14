import pytest
from sugarcode.extra_doc.frame_layout import layout as f, NOT_CLAIMED

F4 = [('a', 3), ('b', 13), ('c', 8), ('d', 1)]


def test_oracle():
    r = f(F4, 4)
    assert [(x['start_bit'], x['end_bit'], x['first_byte'], x['last_byte']) for x in r['fields']] == [
        (0, 3, 0, 0), (3, 16, 0, 1), (16, 24, 2, 2), (24, 25, 3, 3)]
    assert (r['used_bits'], r['total_bytes'], r['padding_bits']) == (25, 4, 7)
    assert all(type(x['first_byte']) is int and type(x['last_byte']) is int for x in r['fields'])
    assert r['protocol_validated'] is False and r['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 8


def test_alignment_effects():
    r = f(F4, 3)
    assert (r['total_bytes'], r['padding_bits']) == (6, 23)
    r = f([('w', 32)], 4)
    assert (r['total_bytes'], r['padding_bits']) == (4, 0)
    r = f([('w', 33)], 4)
    assert (r['total_bytes'], r['padding_bits']) == (8, 31)
    assert f([('x', 1)], 1)['total_bytes'] == 1


def test_bounds_ok():
    r = f([('f%d' % i, 64) for i in range(20)], 16)
    assert r['used_bits'] == 1280 and r['total_bytes'] == 160
    assert f([('n' * 40, 64)], 16)['total_bytes'] == 16


@pytest.mark.parametrize('args,exc,msg', [
    ((F4, True), TypeError, 'alignment'), ((F4, 1.0), TypeError, 'alignment'),
    ((F4, 0), ValueError, 'alignment'), ((F4, 17), ValueError, 'alignment'),
    (('x', 1), TypeError, 'list or tuple'), (([], 1), ValueError, 'field count'),
    (([('a', 1)] * 21, 1), ValueError, 'field count'),
    (([('a',)], 1), ValueError, 'each field'), ((['ab'], 1), ValueError, 'each field'),
    (([{'a': 1}], 1), ValueError, 'each field'),
    (([(1, 1)], 1), TypeError, 'names must be str'), (([('', 1)], 1), ValueError, '1 to 40'),
    (([('x' * 41, 1)], 1), ValueError, '1 to 40'),
    (([('a', True)], 1), TypeError, 'bits'), (([('a', 1.0)], 1), TypeError, 'bits'),
    (([('a', 0)], 1), ValueError, 'bits must'), (([('a', 65)], 1), ValueError, 'bits must'),
    (([('a', 1), ('a', 2)], 1), ValueError, 'unique'),
])
def test_refusals(args, exc, msg):
    with pytest.raises(exc, match=msg):
        f(*args)


def test_cap_before_scan():
    with pytest.raises(ValueError, match='field count'):
        f(['x'] * 10 ** 6, 1)
