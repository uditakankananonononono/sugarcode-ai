import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.cache_sim import simulate_cache as f, NOT_CLAIMED

T = ['a', 'b', 'a', 'c', 'b']


def test_lru_oracle():
    r = f(T, 2, 'lru', 1, 11)
    assert r['accesses'] == ['miss', 'miss', 'hit', 'miss', 'miss']
    assert (r['hits'], r['misses'], r['hit_ratio'], r['evictions']) == (1, 4, F(1, 5), 2)
    assert r['final_contents'] == ('c', 'b') and r['average_ms'] == 9 and r['no_cache_ms'] == 11
    assert r['speedup'] == F(11, 9)
    assert r['strategy_validated'] is False and r['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 7


def test_fifo_oracle():
    r = f(T, 2, 'fifo', 1, 11)
    assert r['accesses'] == ['miss', 'miss', 'hit', 'miss', 'hit']
    assert (r['hits'], r['evictions'], r['final_contents'], r['average_ms'], r['speedup']) == (2, 1, ('b', 'c'), 7, F(11, 7))


def test_zero_latency_speedup_none():
    assert f(T, 2, 'lru', 0, 0)['speedup'] is None


def test_capacity_one_and_big():
    r = f(['a', 'a', 'b', 'a'], 1, 'lru', 0, 4)
    assert r['accesses'] == ['miss', 'hit', 'miss', 'miss'] and r['evictions'] == 2
    r = f(['a', 'b'], 50, 'fifo', 0, 4)
    assert r['evictions'] == 0 and r['final_contents'] == ('a', 'b')


def test_bounds_ok():
    f(['k' * 20] * 200, 50, 'lru', 10 ** 6, 10 ** 6)
    f(['a'], 1, 'lru', 5, 5)


@pytest.mark.parametrize('args,exc,msg', [
    ((T, True, 'lru', 1, 2), TypeError, 'capacity'), ((T, 1.0, 'lru', 1, 2), TypeError, 'capacity'),
    ((T, 0, 'lru', 1, 2), ValueError, 'capacity'), ((T, 51, 'lru', 1, 2), ValueError, 'capacity'),
    ((T, 2, 'lru', True, 2), TypeError, 'hit_ms'), ((T, 2, 'lru', 1, True), TypeError, 'miss_ms'),
    ((T, 2, 'lru', 1.0, 2), TypeError, 'hit_ms'), ((T, 2, 'lru', 1, 2.0), TypeError, 'miss_ms'),
    ((T, 2, 'lru', -1, 2), ValueError, 'hit_ms'), ((T, 2, 'lru', 1, 10 ** 6 + 1), ValueError, 'miss_ms'),
    ((T, 2, 'lru', 10 ** 6 + 1, 10 ** 6 + 1), ValueError, 'hit_ms'),
    ((T, 2, 'lru', 3, 2), ValueError, 'must not exceed'),
    ((T, 2, 1, 1, 2), TypeError, 'policy must be str'), ((T, 2, 'LRU', 1, 2), ValueError, "'lru' or 'fifo'"),
    (('abc', 2, 'lru', 1, 2), TypeError, 'list or tuple'), (({'a'}, 2, 'lru', 1, 2), TypeError, 'list or tuple'),
    (([], 2, 'lru', 1, 2), ValueError, 'trace length'), ((['a'] * 201, 2, 'lru', 1, 2), ValueError, 'trace length'),
    (([1], 2, 'lru', 1, 2), TypeError, 'trace keys'), (([''], 2, 'lru', 1, 2), ValueError, '1 to 20'),
    ((['k' * 21], 2, 'lru', 1, 2), ValueError, '1 to 20'),
])
def test_refusals(args, exc, msg):
    with pytest.raises(exc, match=msg):
        f(*args)


def test_cap_before_scan():
    with pytest.raises(ValueError, match='trace length'):
        f([1] * 10 ** 6, 2, 'lru', 1, 2)
