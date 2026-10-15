import pathlib
import random
from fractions import Fraction

import pytest

from sugarcode.extra_doc import lz_complexity2010 as mod

ROOT = pathlib.Path(mod.__file__).parent


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


class S(str):
    pass


def test_scope_and_constants():
    assert mod.SCOPE == 'PARTIAL: Lempel-Ziv 1976 phrase parsing of one supplied binary word, no randomness or entropy claim'
    assert mod.NOT_CLAIMED == ('randomness tests', 'entropy estimates', 'data compression claims',
                               'production readiness')
    assert 'NOT_CLAIMED' in mod.__doc__ and not (ROOT / '__init__.py').exists()
    assert (mod.MIN_WORD, mod.MAX_WORD) == (1, 60)


def _ks_count(s):
    """Independent: the Kaspar-Schuster counter algorithm (no substring search, no phrase list)."""
    n = len(s)
    if n == 1:
        return 1
    c, l, i, k, kmax = 1, 1, 0, 1, 1
    while True:
        if s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n:
                c += 1
                break
        else:
            kmax = max(k, kmax)
            i += 1
            if i == l:
                c += 1
                l += kmax
                if l + 1 > n:
                    break
                i, k, kmax = 0, 1, 1
            else:
                k = 1
    return c


def test_worked_examples():
    # the example from Kaspar and Schuster (1987): 0.001.10.100.1000.101
    r = mod.lz_complexity('0001101001000101')
    assert r == {'length': 16, 'phrases': ['0', '001', '10', '100', '1000', '101'], 'complexity': 6,
                 'longest': 4, 'ratio': Fraction(3, 8)}
    assert type(r['ratio']) is Fraction and list(r) == ['length', 'phrases', 'complexity', 'longest', 'ratio']
    assert mod.lz_complexity('0') == {'length': 1, 'phrases': ['0'], 'complexity': 1, 'longest': 1, 'ratio': Fraction(1)}
    assert mod.lz_complexity('01')['phrases'] == ['0', '1']
    assert mod.lz_complexity('1111')['phrases'] == ['1', '111']
    assert mod.lz_complexity('0000000')['phrases'] == ['0', '000000']
    assert mod.lz_complexity('0101')['phrases'] == ['0', '1', '01']
    assert mod.lz_complexity('0110')['phrases'] == ['0', '1', '10']
    assert mod.lz_complexity('0011')['phrases'] == ['0', '01', '1']
    # phrases may overlap themselves, and the last phrase may be a repeat
    assert mod.lz_complexity('0010')['phrases'] == ['0', '01', '0']
    assert mod.lz_complexity('01' * 30)['phrases'] == ['0', '1', '01' * 29]
    assert mod.lz_complexity('1' * 60)['complexity'] == 2


def test_randomized_against_counter_algorithm_and_invariants():
    rng = random.Random(2010)
    for _ in range(3000):
        n = rng.randint(1, 60)
        p = rng.choice([.5, .1, .9, 0.0, 1.0])
        w = ''.join('1' if rng.random() < p else '0' for _ in range(n))
        r = mod.lz_complexity(w)
        assert r['complexity'] == _ks_count(w) == len(r['phrases'])
        assert ''.join(r['phrases']) == w and r['length'] == n
        assert r['longest'] == max(map(len, r['phrases']))
        assert r['ratio'] == Fraction(len(r['phrases']), n)


def test_validation_messages_boundaries_and_order():
    WT = 'word must be a string'
    WS = 'word must hold 1 to 60 characters'
    for bad in (None, 5, b'01', ['0'], ('0',), {}):
        _raises(TypeError, WT, mod.lz_complexity, bad)
    _raises(ValueError, WS, mod.lz_complexity, '')
    _raises(ValueError, WS, mod.lz_complexity, '0' * 61)
    assert mod.lz_complexity('0' * 60)['length'] == 60 and mod.lz_complexity('1')['length'] == 1
    _raises(ValueError, "character 1: expected '0' or '1'", mod.lz_complexity, '2')
    _raises(ValueError, "character 3: expected '0' or '1'", mod.lz_complexity, '01x')
    _raises(ValueError, "character 2: expected '0' or '1'", mod.lz_complexity, '0\u0661')
    _raises(ValueError, "character 2: expected '0' or '1'", mod.lz_complexity, '1 ')
    _raises(ValueError, "character 1: expected '0' or '1'", mod.lz_complexity, 'a' * 60)
    _raises(ValueError, "character 1: expected '0' or '1'", mod.lz_complexity, '\u00c9')
    _raises(ValueError, "character 1: expected '0' or '1'", mod.lz_complexity, '\u0130')
    _raises(ValueError, "character 1: expected '0' or '1'", mod.lz_complexity, '\u212a')
    _raises(ValueError, "character 2: expected '0' or '1'", mod.lz_complexity, "0'")
    _raises(TypeError, WT, mod.lz_complexity, S('0101'))
    _raises(TypeError, WT, mod.lz_complexity, 5)
    _raises(ValueError, WS, mod.lz_complexity, '2' * 61)
    _raises(ValueError, "character 2: expected '0' or '1'", mod.lz_complexity, '0' + '2' + '3')
