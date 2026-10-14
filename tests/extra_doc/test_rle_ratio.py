import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.rle_ratio import rle as f, NOT_CLAIMED


def test_oracle():
    r = f('aaabccdddd')
    assert r['runs'] == [('a', 3), ('b', 1), ('c', 2), ('d', 4)] and r['run_count'] == 4
    assert (r['original_length'], r['encoded_units'], r['ratio'], r['round_trip_ok']) == (10, 8, F(4, 5), True)
    assert r['compression_validated'] is False and r['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 7


def test_edges():
    assert f('x')['ratio'] == 2 and f('abab')['ratio'] == 2
    r = f('3a3  \n')
    assert r['runs'] == [('3', 1), ('a', 1), ('3', 1), (' ', 2), ('\n', 1)] and r['round_trip_ok'] is True
    r = f('z' * 500)
    assert r['runs'] == [('z', 500)] and r['ratio'] == F(1, 250)


@pytest.mark.parametrize('arg,exc,msg', [
    (b'abc', TypeError, 'must be str'), (None, TypeError, 'must be str'), (['a'], TypeError, 'must be str'),
    ('', ValueError, 'between 1 and 500'), ('a' * 501, ValueError, 'between 1 and 500'),
])
def test_refusals(arg, exc, msg):
    with pytest.raises(exc, match=msg):
        f(arg)
