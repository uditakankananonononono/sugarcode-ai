import pytest
from fractions import Fraction as F
from sugarcode.extra_doc.packet_overhead import encapsulate as f, NOT_CLAIMED


def test_oracle():
    r = f(3000, [14, 20, 20], 1500)
    assert (r['header_total'], r['payload_per_fragment'], r['fragments'], r['wire_bytes']) == (54, 1446, 3, 3162)
    assert r['efficiency'] == F(500, 527)
    assert r['stack_validated'] is False and r['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 6


def test_fragment_boundaries():
    assert f(1446, [54], 1500)['fragments'] == 1
    assert f(1447, [54], 1500)['fragments'] == 2
    assert f(2892, [54], 1500)['fragments'] == 2
    assert f(2893, [54], 1500)['fragments'] == 3


def test_zero_payload_and_zero_wire():
    r = f(0, [10], 100)
    assert r['fragments'] == 1 and r['wire_bytes'] == 10 and r['efficiency'] == 0
    r = f(0, [0], 1)
    assert r['wire_bytes'] == 0 and r['efficiency'] is None and r['payload_per_fragment'] == 1


def test_bounds_ok():
    f(10 ** 7, [1000] * 8, 65535)
    f(10 ** 7, [0] * 8, 1)
    f(5, [1000], 1001)
    f(0, [1] * 8, 9)


@pytest.mark.parametrize('args,exc,msg', [
    ((True, [1], 100), TypeError, 'payload'), ((1.0, [1], 100), TypeError, 'payload'),
    ((-1, [1], 100), ValueError, 'payload'), ((10 ** 7 + 1, [1], 100), ValueError, 'payload'),
    ((1, [1], True), TypeError, 'limit'), ((1, [1], 1.0), TypeError, 'limit'),
    ((1, [1], 0), ValueError, 'limit'), ((1, [1], 65536), ValueError, 'limit'),
    ((1, 'x', 100), TypeError, 'list or tuple'), ((1, {1}, 100), TypeError, 'list or tuple'),
    ((1, [], 100), ValueError, 'layer count'), ((1, [1] * 9, 100), ValueError, 'layer count'),
    ((1, [True], 100), TypeError, 'header sizes'), ((1, [1.0], 100), TypeError, 'header sizes'),
    ((1, [-1], 100), ValueError, 'header sizes'), ((1, [1001], 2000), ValueError, 'header sizes'),
    ((1, [100], 100), ValueError, 'below the limit'), ((1, [60, 60], 100), ValueError, 'below the limit'),
])
def test_refusals(args, exc, msg):
    with pytest.raises(exc, match=msg):
        f(*args)


def test_cap_before_scan():
    with pytest.raises(ValueError, match='layer count'):
        f(1, ['x'] * 10 ** 6, 100)
