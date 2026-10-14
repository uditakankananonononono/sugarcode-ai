import itertools
import pytest
from sugarcode.extra_doc.hamming74 import encode, decode, NOT_CLAIMED


def test_hand_literals():
    assert encode([1, 0, 1, 1])['codeword'] == (0, 1, 1, 0, 0, 1, 1)
    assert encode([0, 0, 0, 0])['codeword'] == (0,) * 7
    assert encode((1, 1, 1, 1))['codeword'] == (1,) * 7
    assert encode([1, 0, 0, 0])['codeword'] == (1, 1, 1, 0, 0, 0, 0)
    r = decode((0, 1, 1, 0, 0, 1, 1))
    assert r['syndrome'] == 0 and r['data'] == (1, 0, 1, 1)
    r = decode((0, 1, 1, 0, 0, 0, 1))
    assert r['syndrome'] == 6 and r['corrected'] == (0, 1, 1, 0, 0, 1, 1) and r['data'] == (1, 0, 1, 1)
    e = encode([1, 0, 1, 1])
    assert e['code_validated'] is False and e['not_claimed'] == NOT_CLAIMED and len(NOT_CLAIMED) == 8
    assert decode((0,) * 7)['code_validated'] is False


def _dist(a, b):
    return sum(x != y for x, y in zip(a, b))


def test_independent_properties():
    words = {d: encode(d)['codeword'] for d in itertools.product((0, 1), repeat=4)}
    assert len(set(words.values())) == 16
    assert min(_dist(a, b) for a, b in itertools.combinations(words.values(), 2)) == 3
    for d, w in words.items():
        assert decode(w)['syndrome'] == 0 and decode(w)['data'] == d
        for i in range(7):
            bad = list(w)
            bad[i] ^= 1
            r = decode(bad)
            assert r['syndrome'] == i + 1 and r['corrected'] == w and r['data'] == d


def test_double_error_miscorrected_and_inputs_untouched():
    w = list(encode([1, 0, 1, 1])['codeword'])
    w[0] ^= 1
    w[1] ^= 1
    r = decode(w)
    assert r['data'] != (1, 0, 1, 1)
    assert w[0] == 1 and w[1] == 0


@pytest.mark.parametrize('fn,arg,exc,msg', [
    (encode, 'abcd', TypeError, 'data must be'), (encode, {1, 0, 1, 1}, TypeError, 'data must be'),
    (encode, [1, 0, 1], ValueError, 'exactly 4'), (encode, [1] * 5, ValueError, 'exactly 4'),
    (encode, [True, 0, 1, 1], TypeError, 'nonbool'), (encode, [1.0, 0, 1, 1], TypeError, 'nonbool'),
    (encode, [2, 0, 1, 1], ValueError, '0 or 1'), (encode, [-1, 0, 1, 1], ValueError, '0 or 1'),
    (decode, 'abcdefg', TypeError, 'word must be'), (decode, [0] * 6, ValueError, 'exactly 7'),
    (decode, [0] * 8, ValueError, 'exactly 7'), (decode, [True] + [0] * 6, TypeError, 'nonbool'),
    (decode, [0.0] * 7, TypeError, 'nonbool'), (decode, [0] * 6 + [2], ValueError, '0 or 1'),
])
def test_refusals(fn, arg, exc, msg):
    with pytest.raises(exc, match=msg):
        fn(arg)


def test_cap_before_scan():
    with pytest.raises(ValueError, match='exactly 7'):
        decode([2] * 10 ** 6)
    with pytest.raises(ValueError, match='exactly 4'):
        encode(['x'] * 10 ** 6)
