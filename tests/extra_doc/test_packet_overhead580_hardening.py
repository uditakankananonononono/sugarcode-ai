"""Row580 hardening: exact-type subclass pins (plain/lying-comparison/
asymmetric-equality int subclasses and IntEnum at payload, limit and header
element slots; list/tuple subclasses at the headers container), refusal-
before-cap, full-message pins by exact equality, an independent arithmetic
oracle, non-adjacent-order and mixed-validity witnesses, boundary accepts,
and a mutation sweep. Tests-only delta: the module already uses exact type()
checks.
"""
import pathlib
import random
import signal
import types
from enum import IntEnum
from fractions import Fraction

import pytest

from sugarcode.extra_doc import packet_overhead as mod

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


class Hdr(IntEnum):
    eth = 14
    huge = 1001


def _oracle(payload, headers, limit):
    total = 0
    for h in headers:
        total += h
    per = limit - total
    q, r = divmod(payload, per)
    frags = q + (1 if r else 0)
    if frags < 1:
        frags = 1
    wire = payload + frags * total
    return {'header_total': total, 'payload_per_fragment': per, 'fragments': frags, 'wire_bytes': wire,
            'efficiency': Fraction(payload, wire) if wire else None}


def _core(m):
    f = m.encapsulate
    r = f(3000, [14, 20, 20], 1500)
    assert (r['header_total'], r['payload_per_fragment'], r['fragments'], r['wire_bytes']) == (54, 1446, 3, 3162)
    assert r['efficiency'] == Fraction(500, 527)
    # fragment boundaries
    assert f(1446, [54], 1500)['fragments'] == 1
    assert f(1447, [54], 1500)['fragments'] == 2
    assert f(2892, [54], 1500)['fragments'] == 2
    assert f(2893, [54], 1500)['fragments'] == 3
    # zero payload and zero wire
    r = f(0, [10], 100)
    assert r['fragments'] == 1 and r['wire_bytes'] == 10 and r['efficiency'] == 0
    r = f(0, [0], 1)
    assert r['wire_bytes'] == 0 and r['efficiency'] is None and r['payload_per_fragment'] == 1
    # tuple headers accepted, exact same result
    assert f(3000, (14, 20, 20), 1500) == f(3000, [14, 20, 20], 1500)
    # header total exactly at the limit is refused; one below is accepted with per == 1
    _raises(V_, 'header total must be below the limit', f, 1, [100], 100)
    assert f(5, [100], 101)['payload_per_fragment'] == 1
    # flags and marker tuple
    r = f(3000, [14, 20, 20], 1500)
    assert r['stack_validated'] is False
    assert r['not_claimed'] == m.NOT_CLAIMED and len(m.NOT_CLAIMED) == 6
    assert m.NOT_CLAIMED[0] == 'any header size matches a real protocol'
    assert m.NOT_CLAIMED[-1] == 'deployment'
    # seeded random cases against the independent oracle
    rng = random.Random(5801)
    for _ in range(120):
        headers = [rng.randint(0, 1000) for _ in range(rng.randint(1, 8))]
        total = sum(headers)
        limit = total + rng.randint(1, 65535 - min(total, 65534)) if total < 65535 else 65535
        payload = rng.randint(0, 10 ** 6)
        assert f(payload, headers, limit) == {**_oracle(payload, headers, limit),
                                              'stack_validated': False, 'not_claimed': m.NOT_CLAIMED}
    # full exact error messages
    _raises(T_, 'payload must be nonbool int', f, True, [1], 100)
    _raises(T_, 'payload must be nonbool int', f, 1.0, [1], 100)
    _raises(V_, 'payload must be between 0 and 10000000', f, -1, [1], 100)
    _raises(V_, 'payload must be between 0 and 10000000', f, 10 ** 7 + 1, [1], 100)
    _raises(T_, 'limit must be nonbool int', f, 1, [1], True)
    _raises(T_, 'limit must be nonbool int', f, 1, [1], 1.0)
    _raises(V_, 'limit must be between 1 and 65535', f, 1, [1], 0)
    _raises(V_, 'limit must be between 1 and 65535', f, 1, [1], 65536)
    _raises(T_, 'headers must be a list or tuple', f, 1, 'x', 100)
    _raises(T_, 'headers must be a list or tuple', f, 1, {1}, 100)
    _raises(V_, 'layer count must be between 1 and 8', f, 1, [], 100)
    _raises(V_, 'layer count must be between 1 and 8', f, 1, [1] * 9, 100)
    _raises(T_, 'header sizes must be nonbool int', f, 1, [True], 100)
    _raises(T_, 'header sizes must be nonbool int', f, 1, [1.0], 100)
    _raises(V_, 'header sizes must be between 0 and 1000', f, 1, [-1], 100)
    _raises(V_, 'header sizes must be between 0 and 1000', f, 1, [1001], 2000)
    _raises(V_, 'header total must be below the limit', f, 1, [60, 60], 100)
    # boundary accepts
    f(10 ** 7, [1000] * 8, 65535)
    f(10 ** 7, [0] * 8, 1)
    f(0, [1] * 8, 9)


def _mix(m):
    f = m.encapsulate
    # ordering: payload before limit before headers; count before element scan; total check last
    _raises(T_, 'payload must be nonbool int', f, 'x', 'y', 'z')
    _raises(V_, 'payload must be between 0 and 10000000', f, -1, 'y', 'z')
    _raises(T_, 'limit must be nonbool int', f, 1, 'y', 'z')
    _raises(V_, 'limit must be between 1 and 65535', f, 1, 'y', 0)  # limit before headers
    _raises(T_, 'headers must be a list or tuple', f, 1, 'y', 100)
    _raises(V_, 'layer count must be between 1 and 8', f, 1, ['x'] * 9, 100)
    _raises(V_, 'layer count must be between 1 and 8', f, 1, ['x'] * 10 ** 6, 100)
    # non-adjacent bad entries and mixed validity after valid earlier entries
    _raises(T_, 'header sizes must be nonbool int', f, 1, [1, 2, 3, 'x'], 100)
    _raises(V_, 'header sizes must be between 0 and 1000', f, 1, [0, 500, 1001], 2000)
    _raises(T_, 'header sizes must be nonbool int', f, 1, [1, PlainInt(2)], 100)
    _raises(T_, 'header sizes must be nonbool int', f, 1, [1, AsymInt(2)], 100)
    _raises(T_, 'payload must be nonbool int', f, PlainInt(5), [1], 100)
    _raises(T_, 'limit must be nonbool int', f, 1, [1], AsymInt(100))
    # oversized header total reported only after all header element errors
    _raises(T_, 'header sizes must be nonbool int', f, 1, [900, 'x'], 1000)


def _late(m):
    f = m.encapsulate
    # container subclasses refused
    _raises(T_, 'headers must be a list or tuple', f, 1, L([1]), 100)
    _raises(T_, 'headers must be a list or tuple', f, 1, T((1,)), 100)
    # int subclasses refused at every int slot, incl. IntEnum and lying comparisons
    _raises(T_, 'payload must be nonbool int', f, LyingCmpInt(5), [1], 100)
    _raises(T_, 'payload must be nonbool int', f, AsymInt(5), [1], 100)
    _raises(T_, 'limit must be nonbool int', f, 1, [1], PlainInt(100))
    _raises(T_, 'limit must be nonbool int', f, 1, [1], LyingCmpInt(100))
    _raises(T_, 'header sizes must be nonbool int', f, 1, [Hdr.eth], 100)
    _raises(T_, 'header sizes must be nonbool int', f, 1, [LyingCmpInt(14)], 100)
    # subclass refused before any cap/range/count check
    _raises(T_, 'headers must be a list or tuple', f, 1, L([1] * 9), 100)
    _raises(T_, 'headers must be a list or tuple', f, 1, T(['x'] * 10 ** 6), 100)
    _raises(T_, 'payload must be nonbool int', f, LyingCmpInt(10 ** 7 + 1), [1], 100)
    _raises(T_, 'payload must be nonbool int', f, LyingCmpInt(-1), [1], 100)
    _raises(T_, 'limit must be nonbool int', f, 1, [1], LyingCmpInt(0))
    _raises(T_, 'limit must be nonbool int', f, 1, [1], LyingCmpInt(65536))
    _raises(T_, 'header sizes must be nonbool int', f, 1, [LyingCmpInt(1001)], 2000)
    _raises(T_, 'header sizes must be nonbool int', f, 1, [Hdr.huge], 2000)
    # exact list-shaped and tuple-shaped acceptance counterparts
    assert f(3000, list([14, 20, 20]), 1500) == f(3000, tuple([14, 20, 20]), 1500)


def battery(m):
    _core(m)
    _mix(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('        if type(v) is not int:', '        if not isinstance(v, int):'),
    ('    if type(headers) not in (list, tuple):', '    if not isinstance(headers, (list, tuple)):'),
    ('        if type(h) is not int:', '        if not isinstance(h, int):'),
    ("('payload', payload, 0, 10 ** 7)", "('payload', payload, 0, 10 ** 8)"),
    ("('limit', limit, 1, 65535)", "('limit', limit, 1, 65536)"),
    ('    if not 1 <= len(headers) <= 8:', '    if not 1 <= len(headers) < 8:'),
    ('        if not 0 <= h <= 1000:', '        if not 0 < h <= 1000:'),
    ('    if total >= limit:', '    if total > limit:'),
    ('    per = limit - total', '    per = limit - total - 1'),
    ('    frags = max(1, -(-payload // per))', '    frags = max(1, payload // per)'),
    ('    frags = max(1, -(-payload // per))', '    frags = -(-payload // per)'),
    ('    wire = payload + frags * total', '    wire = payload + total'),
    ("'efficiency': Fraction(payload, wire) if wire else None,",
     "'efficiency': Fraction(wire, payload) if wire else None,"),
    ("'efficiency': Fraction(payload, wire) if wire else None,",
     "'efficiency': Fraction(payload, wire),"),
    ("'stack_validated': False,", "'stack_validated': True,"),
    ("'not_claimed': NOT_CLAIMED}", "'not_claimed': ()}"),
    ("' must be nonbool int'", "' must be an int'"),
    ("'%s must be between %d and %d' % (label, lo, hi)", "'%s must be between %d and %d' % (label, hi, lo)"),
    ("'headers must be a list or tuple'", "'headers must be a list'"),
    ("'layer count must be between 1 and 8'", "'layer count must be between 1 and 7'"),
    ("'header sizes must be nonbool int'", "'header sizes must be ints'"),
    ("'header sizes must be between 0 and 1000'", "'header sizes must be between 0 and 999'"),
    ("'header total must be below the limit'", "'header total must be at most the limit'"),
    ('    total = sum(headers)', '    total = sum(headers) + 1'),
    ("for label, v, lo, hi in (('payload', payload, 0, 10 ** 7), ('limit', limit, 1, 65535)):",
     "for label, v, lo, hi in (('limit', limit, 1, 65535), ('payload', payload, 0, 10 ** 7)):"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
