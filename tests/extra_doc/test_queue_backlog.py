import pytest
from sugarcode.extra_doc.queue_backlog import simulate_queue as f, NOT_CLAIMED


def test_oracle():
    r = f([5, 10, 0, 0], 3, 6)
    assert r['ticks'] == [{'arrived': 5, 'dropped': 0, 'served': 3, 'backlog': 2},
                          {'arrived': 10, 'dropped': 6, 'served': 3, 'backlog': 3},
                          {'arrived': 0, 'dropped': 0, 'served': 3, 'backlog': 0},
                          {'arrived': 0, 'dropped': 0, 'served': 0, 'backlog': 0}]
    assert (r['total_served'], r['total_dropped'], r['max_backlog'], r['drain_ticks']) == (9, 6, 3, 0)
    assert r['queue_validated'] is False and r['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 6


def test_drain():
    assert f([10], 3, 10)['drain_ticks'] == 3
    assert f([9], 3, 10)['drain_ticks'] == 2
    assert f([2], 0, 5)['drain_ticks'] is None
    assert f([0], 0, 5)['drain_ticks'] == 0


def test_capacity_zero_and_exact_fill():
    r = f([4], 2, 0)
    assert r['total_dropped'] == 4 and r['total_served'] == 0
    r = f([6, 0], 0, 6)
    assert r['total_dropped'] == 0 and r['max_backlog'] == 6
    r = f([7], 0, 6)
    assert r['total_dropped'] == 1


def test_bounds_ok():
    f([10 ** 6] * 100, 10 ** 6, 10 ** 6)
    assert f([10 ** 6], 0, 10 ** 6)['max_backlog'] == 10 ** 6


@pytest.mark.parametrize('args,exc,msg', [
    (([1], True, 1), TypeError, 'service'), (([1], 1.0, 1), TypeError, 'service'),
    (([1], 1, True), TypeError, 'capacity'), (([1], 1, 1.0), TypeError, 'capacity'),
    (([1], -1, 1), ValueError, 'service'), (([1], 10 ** 6 + 1, 1), ValueError, 'service'),
    (([1], 1, -1), ValueError, 'capacity'), (([1], 1, 10 ** 6 + 1), ValueError, 'capacity'),
    (('x', 1, 1), TypeError, 'list or tuple'), (({1}, 1, 1), TypeError, 'list or tuple'),
    (([], 1, 1), ValueError, 'tick count'), (([1] * 101, 1, 1), ValueError, 'tick count'),
    (([True], 1, 1), TypeError, 'arrivals'), (([1.0], 1, 1), TypeError, 'arrivals'),
    (([-1], 1, 1), ValueError, 'arrivals'), (([10 ** 6 + 1], 1, 1), ValueError, 'arrivals'),
])
def test_refusals(args, exc, msg):
    with pytest.raises(exc, match=msg):
        f(*args)


def test_cap_before_scan():
    with pytest.raises(ValueError, match='tick count'):
        f(['x'] * 10 ** 6, 1, 1)
