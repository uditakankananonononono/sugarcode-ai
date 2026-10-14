"""Row581 hardening: exact-type subclass pins (int subclasses incl. IntEnum and
lying-comparison ints at the alignment and bits slots; str subclasses at the
name slot; list/tuple subclasses at the fields container and field pairs),
refusal-before-cap, full-message pins by exact equality (including the
ValueError class of the pair-shape refusal), an independent layout oracle,
non-adjacent-order and mixed-validity witnesses, boundary accepts, and a
mutation sweep. Tests-only delta: the module already uses exact type() checks.
"""
import pathlib
import random
import signal
import types
from collections import namedtuple
from enum import IntEnum

import pytest

from sugarcode.extra_doc import frame_layout as mod

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


class S(str):
    pass


class WeirdStr(str):
    def __eq__(self, other):
        return True

    def __hash__(self):
        return 0


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


class Bits(IntEnum):
    byte = 8
    huge = 65


Field = namedtuple('Field', 'name bits')
F4 = [('a', 3), ('b', 13), ('c', 8), ('d', 1)]


def _oracle(fields, alignment):
    rows = []
    pos = 0
    for name, bits in fields:
        rows.append({'name': name, 'start_bit': pos, 'end_bit': pos + bits,
                     'first_byte': (pos // 16) * 2 if False else pos // 8,
                     'last_byte': (pos + bits - 1) // 8})
        pos += bits
    span = 8 * alignment
    total = ((pos + span - 1) // span) * alignment
    return {'fields': rows, 'used_bits': pos, 'total_bytes': total,
            'padding_bits': total * 8 - pos}


def _core(m):
    f = m.layout
    r = f(F4, 4)
    assert [(x['start_bit'], x['end_bit'], x['first_byte'], x['last_byte']) for x in r['fields']] == [
        (0, 3, 0, 0), (3, 16, 0, 1), (16, 24, 2, 2), (24, 25, 3, 3)]
    assert (r['used_bits'], r['total_bytes'], r['padding_bits']) == (25, 4, 7)
    r = f(F4, 3)
    assert (r['total_bytes'], r['padding_bits']) == (6, 23)
    assert (f([('w', 32)], 4)['total_bytes'], f([('w', 32)], 4)['padding_bits']) == (4, 0)
    assert (f([('w', 33)], 4)['total_bytes'], f([('w', 33)], 4)['padding_bits']) == (8, 31)
    assert f([('x', 1)], 1)['total_bytes'] == 1
    # a field of exactly 8*k bits ends on a byte edge; last_byte points at its final bit
    r = f([('e', 8)], 1)
    assert (r['fields'][0]['end_bit'], r['fields'][0]['last_byte']) == (8, 0)
    # tuple container and tuple/list pairs accepted identically
    assert f(tuple(F4), 4) == f(F4, 4) == f([list(x) for x in F4], 4)
    # names allow any characters (no charset restriction), length 1..40
    assert f([('!@# $%^', 1), ('\n\t', 2)], 1)['used_bits'] == 3
    # flags and marker tuple
    assert r['protocol_validated'] is False
    assert r['not_claimed'] == m.NOT_CLAIMED and len(m.NOT_CLAIMED) == 8
    assert m.NOT_CLAIMED[0] == 'layout matches any real protocol' and m.NOT_CLAIMED[-1] == 'deployment'
    # seeded random cases against the independent oracle
    rng = random.Random(5811)
    for _ in range(120):
        nf = rng.randint(1, 10)
        names = rng.sample('abcdefghij', nf)
        fields = [(nm, rng.randint(1, 64)) for nm in names]
        al = rng.randint(1, 16)
        assert f(fields, al) == {**_oracle(fields, al),
                                 'protocol_validated': False, 'not_claimed': m.NOT_CLAIMED}
    # full exact error messages
    _raises(T_, 'alignment must be nonbool int', f, F4, True)
    _raises(T_, 'alignment must be nonbool int', f, F4, 1.0)
    _raises(V_, 'alignment must be between 1 and 16', f, F4, 0)
    _raises(V_, 'alignment must be between 1 and 16', f, F4, 17)
    _raises(T_, 'fields must be a list or tuple', f, 'x', 1)
    _raises(V_, 'field count must be between 1 and 20', f, [], 1)
    _raises(V_, 'field count must be between 1 and 20', f, [('a', 1)] * 21, 1)
    _raises(V_, 'each field must be (name, bits)', f, [('a',)], 1)
    _raises(V_, 'each field must be (name, bits)', f, ['ab'], 1)
    _raises(V_, 'each field must be (name, bits)', f, [('a', 1, 2)], 1)
    _raises(T_, 'names must be str', f, [(1, 1)], 1)
    _raises(V_, 'names must be 1 to 40 characters', f, [('', 1)], 1)
    _raises(V_, 'names must be 1 to 40 characters', f, [('x' * 41, 1)], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', True)], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', 1.0)], 1)
    _raises(V_, 'bits must be between 1 and 64', f, [('a', 0)], 1)
    _raises(V_, 'bits must be between 1 and 64', f, [('a', 65)], 1)
    _raises(V_, 'field names must be unique', f, [('a', 1), ('a', 2)], 1)
    # boundary accepts
    r = f([('f%d' % i, 64) for i in range(20)], 16)
    assert r['used_bits'] == 1280 and r['total_bytes'] == 160
    assert f([('n' * 40, 64)], 16)['total_bytes'] == 16


def _mix(m):
    f = m.layout
    # ordering: alignment before fields; count before scan; pair shape before name/bits; unique last
    _raises(T_, 'alignment must be nonbool int', f, 'y', 'z')
    _raises(V_, 'alignment must be between 1 and 16', f, 'y', 0)
    _raises(V_, 'field count must be between 1 and 20', f, ['x'] * 21, 1)
    _raises(V_, 'field count must be between 1 and 20', f, ['x'] * 10 ** 6, 1)
    _raises(V_, 'each field must be (name, bits)', f, [5, (0, 0)], 1)
    _raises(V_, 'each field must be (name, bits)', f, [(1,), (2, 'y')], 1)
    _raises(T_, 'names must be str', f, [(1, 'x'), ('b', 'y')], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', 'x'), (0, 'y')], 1)
    _raises(V_, 'bits must be between 1 and 64', f, [('a', 0), ('b', -1)], 1)
    # uniqueness checked only after every field validates
    _raises(V_, 'each field must be (name, bits)', f, [('a', 1), ('a', 1), 9], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', 1), ('a', 'x')], 1)
    # non-adjacent duplicates and mixed validity after valid earlier entries
    _raises(V_, 'field names must be unique', f, [('a', 1), ('b', 1), ('c', 1), ('a', 2)], 1)
    _raises(T_, 'names must be str', f, [('a', 1), ('b', 1), (S('c'), 1)], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', 1), ('b', PlainInt(2))], 1)
    _raises(V_, 'each field must be (name, bits)', f, [('a', 1), ('b', 2), L(['c', 3])], 1)


def _late(m):
    f = m.layout
    # container and pair subclasses refused (pair-shape refusal is ValueError by contract)
    _raises(T_, 'fields must be a list or tuple', f, L(F4), 1)
    _raises(T_, 'fields must be a list or tuple', f, T(F4), 1)
    _raises(V_, 'each field must be (name, bits)', f, [L(['a', 1])], 1)
    _raises(V_, 'each field must be (name, bits)', f, [T(('a', 1))], 1)
    _raises(V_, 'each field must be (name, bits)', f, [Field('a', 1)], 1)
    # str and int subclasses refused at name/bits/alignment slots, incl. IntEnum and lying comparisons
    _raises(T_, 'names must be str', f, [(S('a'), 1)], 1)
    _raises(T_, 'names must be str', f, [(WeirdStr('a'), 1)], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', PlainInt(8))], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', AsymInt(8))], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', Bits.byte)], 1)
    _raises(T_, 'alignment must be nonbool int', f, F4, PlainInt(4))
    _raises(T_, 'alignment must be nonbool int', f, F4, LyingCmpInt(4))
    _raises(T_, 'alignment must be nonbool int', f, F4, AsymInt(4))
    # subclass refused before any cap/range/count check
    _raises(T_, 'fields must be a list or tuple', f, L([('a', 1)] * 21), 1)
    _raises(T_, 'fields must be a list or tuple', f, T(['x'] * 10 ** 6), 1)
    _raises(T_, 'alignment must be nonbool int', f, F4, LyingCmpInt(0))
    _raises(T_, 'alignment must be nonbool int', f, F4, LyingCmpInt(17))
    _raises(T_, 'bits must be nonbool int', f, [('a', LyingCmpInt(0))], 1)
    _raises(T_, 'bits must be nonbool int', f, [('a', Bits.huge)], 1)
    _raises(T_, 'names must be str', f, [(S('x' * 41), 1)], 1)
    # exact list-shaped and tuple-shaped acceptance counterparts
    assert f(list([list(['a', 3]), list(['b', 13])]), 4) == f(tuple([tuple(['a', 3]), tuple(['b', 13])]), 4)


def battery(m):
    _core(m)
    _mix(m)
    _late(m)


def test_battery_on_real_module():
    battery(mod)


MUTANTS = [
    ('    if type(alignment) is not int:', '    if not isinstance(alignment, int):'),
    ('    if type(fields) not in (list, tuple):', '    if not isinstance(fields, (list, tuple)):'),
    ('        if type(f) not in (list, tuple) or len(f) != 2:',
     '        if not isinstance(f, (list, tuple)) or len(f) != 2:'),
    ('        if type(f) not in (list, tuple) or len(f) != 2:',
     '        if type(f) not in (list, tuple) or len(f) != 3:'),
    ("            raise ValueError('each field must be (name, bits)')",
     "            raise TypeError('each field must be (name, bits)')"),
    ('        if type(name) is not str:', '        if not isinstance(name, str):'),
    ('        if type(bits) is not int:', '        if not isinstance(bits, int):'),
    ('    if not 1 <= alignment <= 16:', '    if not 1 <= alignment <= 17:'),
    ('    if not 1 <= len(fields) <= 20:', '    if not 1 <= len(fields) <= 21:'),
    ('        if not 1 <= len(name) <= 40:', '        if not 1 <= len(name) <= 41:'),
    ('        if not 1 <= bits <= 64:', '        if not 1 <= bits <= 65:'),
    ('    if len({r[0] for r in rows}) != len(rows):', '    if len({r[0] for r in rows}) == len(rows):'),
    ("                    'first_byte': pos // 8, 'last_byte': (pos + bits - 1) // 8})",
     "                    'first_byte': pos // 8, 'last_byte': (pos + bits) // 8})"),
    ("                    'first_byte': pos // 8, 'last_byte': (pos + bits - 1) // 8})",
     "                    'first_byte': pos // 16, 'last_byte': (pos + bits - 1) // 8})"),
    ('        pos += bits', '        pos += 1'),
    ('    unit = 8 * alignment', '    unit = 4 * alignment'),
    ('    total = -(-pos // unit) * alignment', '    total = (pos // unit) * alignment'),
    ("'padding_bits': total * 8 - pos,", "'padding_bits': total * 8 - pos - 1,"),
    ("'used_bits': pos,", "'used_bits': pos + 1,"),
    ("        out.append({'name': name, 'start_bit': pos, 'end_bit': pos + bits,",
     "        out.append({'name': name, 'start_bit': pos, 'end_bit': pos + bits + 1,"),
    ("'protocol_validated': False,", "'protocol_validated': True,"),
    ("'alignment must be nonbool int'", "'alignment must be an int'"),
    ("'alignment must be between 1 and 16'", "'alignment must be between 1 and 15'"),
    ("'fields must be a list or tuple'", "'fields must be a list'"),
    ("'field count must be between 1 and 20'", "'field count must be between 1 and 19'"),
    ("'each field must be (name, bits)'", "'each field must be a (name, bits) pair'"),
    ("'names must be str'", "'names must be strings'"),
    ("'names must be 1 to 40 characters'", "'names must be 1 to 39 characters'"),
    ("'bits must be nonbool int'", "'bits must be an int'"),
    ("'bits must be between 1 and 64'", "'bits must be between 1 and 63'"),
    ("'field names must be unique'", "'field names must not repeat'"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)
