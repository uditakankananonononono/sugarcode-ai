"""Row582 hardening: exact-type subclass pins (str subclass and a lying
__eq__/__hash__ str subclass at the text slot), refusal-before-cap, full-
message pins by exact equality, an independent itertools.groupby oracle plus
exhaustive small-alphabet coverage, boundary accepts, and a mutation sweep.
Tests-only delta: the module already uses exact type() checks. No int-typed
input slot exists, so int-subclass/IntEnum pins are N/A.

Equivalent mutants documented (not chased):
  - "'round_trip_ok': back == text" -> "True": round_trip_ok is True for every
    accepted input by construction (back is rebuilt from the runs of that same
    text), so a constant-True mutant is unobservable in a single-mutation
    sweep; the battery still pins the True value on every case.
"""
import itertools
import pathlib
import random
import signal
import types
from fractions import Fraction

import pytest

from sugarcode.extra_doc import rle_ratio as mod

SRC = pathlib.Path(mod.__file__).read_text()
T_, V_ = TypeError, ValueError


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')  # a syntax error is not a kill
    def _timeout(*_):
        raise TimeoutError('mutant did not terminate')
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return True


class S(str):
    pass


class WeirdStr(str):
    def __eq__(self, other):
        return True

    def __hash__(self):
        return 0


def _oracle(text):
    runs = [(ch, sum(1 for _ in grp)) for ch, grp in itertools.groupby(text)]
    n = len(runs)
    return {'runs': runs, 'run_count': n, 'original_length': len(text),
            'encoded_units': 2 * n, 'ratio': Fraction(2 * n, len(text)),
            'round_trip_ok': ''.join(c * k for c, k in runs) == text}


def _core(m):
    f = m.rle
    r = f('aaabccdddd')
    assert r['runs'] == [('a', 3), ('b', 1), ('c', 2), ('d', 4)] and r['run_count'] == 4
    assert (r['original_length'], r['encoded_units'], r['ratio'], r['round_trip_ok']) == (10, 8, Fraction(4, 5), True)
    assert f('x')['ratio'] == 2 and f('abab')['ratio'] == 2
    r = f('3a3  \n')
    assert r['runs'] == [('3', 1), ('a', 1), ('3', 1), (' ', 2), ('\n', 1)] and r['round_trip_ok'] is True
    r = f('z' * 500)
    assert r['runs'] == [('z', 500)] and r['ratio'] == Fraction(1, 250) and r['run_count'] == 1
    # runs are tuples, not lists
    assert all(type(x) is tuple for x in f('aabb')['runs'])
    # alternating maximal run count
    r = f('ab' * 250)
    assert r['run_count'] == 500 and r['ratio'] == 2
    # flags and marker tuple
    assert r['compression_validated'] is False
    assert r['not_claimed'] == m.NOT_CLAIMED and len(m.NOT_CLAIMED) == 7
    assert m.NOT_CLAIMED[0] == 'size model is any real file or wire size' and m.NOT_CLAIMED[-1] == 'deployment'
    # exhaustive small alphabet, lengths 1..7
    for ln in range(1, 8):
        for tup in itertools.product('abc', repeat=ln):
            text = ''.join(tup)
            assert f(text) == {**_oracle(text),
                               'compression_validated': False, 'not_claimed': m.NOT_CLAIMED}
    # seeded random strings with run bias
    rng = random.Random(5821)
    for _ in range(150):
        text = ''.join(rng.choice('aabbccdd \n') for _ in range(rng.randint(1, 60)))
        assert f(text) == {**_oracle(text),
                           'compression_validated': False, 'not_claimed': m.NOT_CLAIMED}
    # full exact error messages
    _raises(T_, 'text must be str', f, b'abc')
    _raises(T_, 'text must be str', f, None)
    _raises(T_, 'text must be str', f, ['a'])
    _raises(T_, 'text must be str', f, 5)
    _raises(V_, 'text length must be between 1 and 500', f, '')
    _raises(V_, 'text length must be between 1 and 500', f, 'a' * 501)
    # boundary accepts
    f('a')
    f('a' * 500)
    f('ab' * 250)


def _mix(m):
    f = m.rle
    # subclass refused before the length cap
    _raises(T_, 'text must be str', f, S('a' * 501))
    _raises(T_, 'text must be str', f, WeirdStr('a' * 501))
    _raises(T_, 'text must be str', f, S(''))
    # a lying __eq__ subclass must never reach the run comparison
    _raises(T_, 'text must be str', f, WeirdStr('aaab'))
    # type check precedes the length check
    _raises(T_, 'text must be str', f, 5)


def battery(m):
    _core(m)
    _mix(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('if type(text) is not str:', 'if not isinstance(text, str):'),
    ('if not 1 <= len(text) <= 500:', 'if not 1 <= len(text) <= 501:'),
    ('if not 1 <= len(text) <= 500:', 'if not 1 <= len(text) < 500:'),
    ('        if runs and runs[-1][0] == ch:', '        if runs and runs[-1][0] != ch:'),
    ('        if runs and runs[-1][0] == ch:', '        if runs[-1][0] == ch:'),
    ('            runs[-1] = (ch, runs[-1][1] + 1)', '            runs[-1] = (ch, runs[-1][1] + 2)'),
    ('            runs[-1] = (ch, runs[-1][1] + 1)', '            runs[-1] = (ch, 1)'),
    ('            runs.append((ch, 1))', '            runs.append((ch, 0))'),
    ('            runs.append((ch, 1))', '            runs.append((ch, 2))'),
    ("    back = ''.join(c * n for c, n in runs)", "    back = ''.join(c * (n + 1) for c, n in runs)"),
    ("    back = ''.join(c * n for c, n in runs)", "    back = ''.join(c for c, n in runs)"),
    ("'encoded_units': 2 * len(runs),", "'encoded_units': len(runs),"),
    ("'ratio': Fraction(2 * len(runs), len(text)),", "'ratio': Fraction(len(text), 2 * len(runs)),"),
    ("'ratio': Fraction(2 * len(runs), len(text)),", "'ratio': Fraction(2 * len(runs), len(text) + 1),"),
    ("'run_count': len(runs),", "'run_count': len(runs) + 1,"),
    ("'original_length': len(text),", "'original_length': len(text) + 1,"),
    ("'compression_validated': False,", "'compression_validated': True,"),
    ("'not_claimed': NOT_CLAIMED}", "'not_claimed': ()}"),
    ("    return {'runs': runs,", "    return {'runs': [list(r) for r in runs],"),
    ("'text must be str'", "'text must be a str'"),
    ("'text length must be between 1 and 500'", "'text length must be between 1 and 499'"),
    ("raise TypeError('text must be str')", "raise ValueError('text must be str')"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
