"""Row583 hardening: exact-type subclass pins (int subclasses incl. IntEnum and
lying-comparison/asymmetric-equality ints at every bit slot; list/tuple
subclasses at the data/word containers), refusal-before-length, full-message
pins by exact equality, an independent oracle built from explicit parity
coverage lists (distinct from the module's i & p bitmask), exhaustive
coverage of all 16 data words and all 128 received words, single-flip
correction for every position of every codeword, the documented double-error
miscorrection, ordering and mixed-validity witnesses, and a mutation sweep.
Tests-only delta: the module already uses exact type() checks.

Equivalent mutants documented (not chased):
  - decode "'corrected': tuple(w[i] for i in sorted(w))" -> "tuple(w[i] for i
    in w)": decode builds w with dict(enumerate(word, 1)), whose insertion
    order is already 1..7, so sorted(w) is a no-op there (in encode, where
    insertion order is 3,5,6,7,1,2,4, the same mutation is shipped and
    killed).
From the extended ad-hoc sweep:
  - encode parity order (1, 2, 4) -> (4, 2, 1): every parity group covers its
    own position plus data positions only (1, 2 and 4 are pairwise
    bit-disjoint, so no other parity position ever enters a group), each
    parity value is therefore independent of computation order, and the
    codeword is emitted via sorted(w) regardless of insertion order.
"""
import itertools
import pathlib
import signal
import types
from enum import IntEnum

import pytest

from sugarcode.extra_doc import hamming74 as mod

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


class L(list):
    pass


class T(tuple):
    pass


class PlainInt(int):
    pass


class LyingCmpInt(int):
    def __ge__(self, other):
        return True

    def __le__(self, other):
        return True


class AsymInt(int):
    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True


class Bit(IntEnum):
    zero = 0
    two = 2


COVER = ((1, (1, 3, 5, 7)), (2, (2, 3, 6, 7)), (4, (4, 5, 6, 7)))


def _oracle_encode(data):
    w = [0] * 8  # 1-indexed
    w[3], w[5], w[6], w[7] = data
    for p, cov in COVER:
        w[p] = sum(w[i] for i in cov if i != p) % 2
    return tuple(w[1:])


def _oracle_decode(word):
    w = [0] + list(word)
    syn = 0
    for p, cov in COVER:
        if sum(w[i] for i in cov) % 2:
            syn += p
    if syn:
        w[syn] = 1 - w[syn]
    return syn, tuple(w[1:]), (w[3], w[5], w[6], w[7])


def _core(m):
    encode, decode = m.encode, m.decode
    # landed literals re-pinned
    assert encode([1, 0, 1, 1])['codeword'] == (0, 1, 1, 0, 0, 1, 1)
    assert encode([0, 0, 0, 0])['codeword'] == (0,) * 7
    assert encode((1, 1, 1, 1))['codeword'] == (1,) * 7
    assert encode([1, 0, 0, 0])['codeword'] == (1, 1, 1, 0, 0, 0, 0)
    r = decode((0, 1, 1, 0, 0, 1, 1))
    assert r['syndrome'] == 0 and r['data'] == (1, 0, 1, 1)
    r = decode((0, 1, 1, 0, 0, 0, 1))
    assert r['syndrome'] == 6 and r['corrected'] == (0, 1, 1, 0, 0, 1, 1) and r['data'] == (1, 0, 1, 1)
    # exhaustive: every data word, every received word
    for data in itertools.product((0, 1), repeat=4):
        assert encode(list(data))['codeword'] == _oracle_encode(data)
    for word in itertools.product((0, 1), repeat=7):
        syn, corr, d = _oracle_decode(word)
        r = decode(list(word))
        assert (r['syndrome'], r['corrected'], r['data']) == (syn, corr, d)
    # every single-bit flip of every codeword is corrected to that codeword
    for data in itertools.product((0, 1), repeat=4):
        w = _oracle_encode(data)
        assert decode(list(w))['syndrome'] == 0
        for i in range(7):
            bad = list(w)
            bad[i] ^= 1
            r = decode(bad)
            assert r['syndrome'] == i + 1 and r['corrected'] == w and r['data'] == data
    # documented double-error miscorrection (a code property, not hidden)
    w = list(_oracle_encode((1, 0, 1, 1)))
    w[0] ^= 1
    w[1] ^= 1
    assert decode(w)['data'] != (1, 0, 1, 1)
    assert (w[0], w[1]) == (1, 0)  # input not mutated
    # min distance 3 across the code
    words = [_oracle_encode(d) for d in itertools.product((0, 1), repeat=4)]
    assert len(set(words)) == 16
    assert min(sum(x != y for x, y in zip(a, b)) for a, b in itertools.combinations(words, 2)) == 3
    # tuple containers accepted identically; outputs are tuples
    assert encode((1, 0, 1, 1)) == encode([1, 0, 1, 1])
    assert type(encode([0, 0, 0, 0])['codeword']) is tuple
    assert type(decode((0,) * 7)['corrected']) is tuple and type(decode((0,) * 7)['data']) is tuple
    # flags and marker tuple
    assert encode([1, 0, 1, 1])['code_validated'] is False
    assert decode((0,) * 7)['code_validated'] is False
    assert encode([1, 0, 1, 1])['not_claimed'] == m.NOT_CLAIMED and len(m.NOT_CLAIMED) == 8
    assert m.NOT_CLAIMED[0] == 'real channels flip single bits' and m.NOT_CLAIMED[-1] == 'deployment'
    # full exact error messages
    _raises(T_, 'data must be a list or tuple', encode, 'abcd')
    _raises(T_, 'data must be a list or tuple', encode, {1, 0, 1, 1})
    _raises(V_, 'data must hold exactly 4 bits', encode, [1, 0, 1])
    _raises(V_, 'data must hold exactly 4 bits', encode, [1] * 5)
    _raises(T_, 'data bits must be nonbool int', encode, [True, 0, 1, 1])
    _raises(T_, 'data bits must be nonbool int', encode, [1.0, 0, 1, 1])
    _raises(V_, 'data bits must be 0 or 1', encode, [2, 0, 1, 1])
    _raises(V_, 'data bits must be 0 or 1', encode, [-1, 0, 1, 1])
    _raises(T_, 'word must be a list or tuple', decode, 'abcdefg')
    _raises(V_, 'word must hold exactly 7 bits', decode, [0] * 6)
    _raises(V_, 'word must hold exactly 7 bits', decode, [0] * 8)
    _raises(T_, 'word bits must be nonbool int', decode, [True] + [0] * 6)
    _raises(V_, 'word bits must be 0 or 1', decode, [0] * 6 + [2])


def _mix(m):
    encode, decode = m.encode, m.decode
    # ordering: container type before length before element scan; elements in order
    _raises(T_, 'data must be a list or tuple', encode, 'xy')
    _raises(V_, 'data must hold exactly 4 bits', encode, ['x'] * 10 ** 6)
    _raises(V_, 'word must hold exactly 7 bits', decode, [2] * 10 ** 6)
    _raises(V_, 'data must hold exactly 4 bits', encode, [2, 'x'])
    # non-adjacent bad entries and mixed validity after valid earlier entries
    _raises(T_, 'data bits must be nonbool int', encode, [0, 1, 'x', 1])
    _raises(V_, 'data bits must be 0 or 1', encode, [0, 1, 1, 2])
    _raises(T_, 'word bits must be nonbool int', decode, [0, 1, 0, PlainInt(1), 0, 1, 0])
    _raises(V_, 'word bits must be 0 or 1', decode, [0, 1, 0, 1, 0, 1, -1])
    _raises(T_, 'data bits must be nonbool int', encode, [0, AsymInt(1), 1, 0])
    _raises(T_, 'word bits must be nonbool int', decode, [Bit.zero] * 7)


def _late(m):
    encode, decode = m.encode, m.decode
    # container subclasses refused
    _raises(T_, 'data must be a list or tuple', encode, L([1, 0, 1, 1]))
    _raises(T_, 'data must be a list or tuple', encode, T((1, 0, 1, 1)))
    _raises(T_, 'word must be a list or tuple', decode, L([0] * 7))
    _raises(T_, 'word must be a list or tuple', decode, T((0,) * 7))
    # int subclasses refused at bit slots, incl. IntEnum and lying comparisons
    _raises(T_, 'data bits must be nonbool int', encode, [PlainInt(1), 0, 1, 1])
    _raises(T_, 'data bits must be nonbool int', encode, [LyingCmpInt(1), 0, 1, 1])
    _raises(T_, 'data bits must be nonbool int', encode, [AsymInt(0), 0, 1, 1])
    _raises(T_, 'data bits must be nonbool int', encode, [Bit.zero, 0, 1, 1])
    _raises(T_, 'word bits must be nonbool int', decode, [LyingCmpInt(0)] + [0] * 6)
    # subclass refused before the length and value checks
    _raises(T_, 'data must be a list or tuple', encode, L([1] * 5))
    _raises(T_, 'data must be a list or tuple', encode, L(['x'] * 10 ** 6))
    _raises(T_, 'word must be a list or tuple', decode, T([2] * 8))
    _raises(T_, 'word must be a list or tuple', decode, T([2] * 10 ** 6))
    _raises(T_, 'data bits must be nonbool int', encode, [LyingCmpInt(2), 0, 1, 1])
    _raises(T_, 'data bits must be nonbool int', encode, [Bit.two, 0, 1, 1])
    _raises(T_, 'word bits must be nonbool int', decode, [LyingCmpInt(-1)] + [0] * 6)
    # exact list-shaped and tuple-shaped acceptance counterparts
    assert encode(list([1, 0, 1, 1])) == encode(tuple([1, 0, 1, 1]))
    assert decode(list([0, 1, 1, 0, 0, 1, 1])) == decode(tuple([0, 1, 1, 0, 0, 1, 1]))


def battery(m):
    _core(m)
    _mix(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('    if type(v) not in (list, tuple):', '    if not isinstance(v, (list, tuple)):'),
    ('        if type(b) is not int:', '        if not isinstance(b, int):'),
    ('    if len(v) != n:', '    if len(v) < n:'),
    ('        if b not in (0, 1):', '        if b not in (0,):'),
    ('    w = {3: data[0], 5: data[1], 6: data[2], 7: data[3]}',
     '    w = {3: data[1], 5: data[0], 6: data[2], 7: data[3]}'),
    ("    for p in (1, 2, 4):\n        w[p] = sum(b for i, b in w.items() if i & p) % 2",
     "    for p in (1, 2, 3):\n        w[p] = sum(b for i, b in w.items() if i & p) % 2"),
    ("        w[p] = sum(b for i, b in w.items() if i & p) % 2",
     "        w[p] = sum(b for i, b in w.items() if i | p) % 2"),
    ("        w[p] = sum(b for i, b in w.items() if i & p) % 2",
     "        w[p] = sum(b for i, b in w.items() if i & p) % 3"),
    ("    return {'codeword': tuple(w[i] for i in sorted(w)),",
     "    return {'codeword': tuple(w[i] for i in w),"),
    ('    w = dict(enumerate(word, 1))', '    w = dict(enumerate(word))'),
    ("    for p in (1, 2, 4):\n        if sum(b for i, b in w.items() if i & p) % 2:",
     "    for p in (1, 2, 4):\n        if sum(b for i, b in w.items() if i | p) % 2:"),
    ("        if sum(b for i, b in w.items() if i & p) % 2:",
     "        if sum(b for i, b in w.items() if i & p) % 2 == 0:"),
    ('            syn += p', '            syn = p'),
    ('        w[syn] ^= 1', '        w[syn] = 1'),
    ('        w[syn] ^= 1', '        w[syn] ^= 0'),
    ("'data': (w[3], w[5], w[6], w[7]),", "'data': (w[3], w[5], w[6], w[6]),"),
    ("'data': (w[3], w[5], w[6], w[7]),", "'data': (w[1], w[3], w[5], w[7]),"),
    ("    for b in v:", "    for b in v[1:]:"),
    ("'code_validated': False, 'not_claimed': NOT_CLAIMED}", "'code_validated': True, 'not_claimed': NOT_CLAIMED}"),
    ("' must be a list or tuple'", "' must be a list'"),
    ("'%s must hold exactly %d bits'", "'%s must hold exactly %d bits.'"),
    ("' bits must be nonbool int'", "' bits must be ints'"),
    ("' bits must be 0 or 1'", "' bits must be 0 or 1 each'"),
    ("raise TypeError(label + ' must be a list or tuple')", "raise ValueError(label + ' must be a list or tuple')"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
