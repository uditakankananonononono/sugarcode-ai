import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import psychoanalytic_criticism as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TM = 'row 1: text must be a string of 1 to 16 characters'
DM = 'row 1: drive must be a string of 1 to 16 characters'
IM = 'row 1: intensity must be a nonbool integer between 1 and 9'


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
    code = compile(mutated, 'mutant', 'exec')
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


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def test_disclaimer_text_exact():
    section = ' '.join(mod.__doc__.split('NOT_CLAIMED:', 1)[1].split())
    assert section == ('the unconscious, repression mechanics, '
                       'clinical validity, Freudian orthodoxy, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: drive tallying over supplied readings'
    assert mod.NOT_CLAIMED == ('the unconscious', 'repression mechanics',
                               'clinical validity', 'Freudian orthodoxy',
                               'production readiness')


def _expected(rows):
    appearances = {}
    energy = {}
    for text, drive, intensity in rows:
        if drive not in appearances:
            appearances[drive] = 0
        appearances[drive] += 1
        if drive not in energy:
            energy[drive] = 0
        energy[drive] += intensity
    most_frequent = None
    rarest = None
    if appearances:
        top = max(appearances.values())
        bottom = min(appearances.values())
        supply = list(dict.fromkeys(d for _t, d, _i in rows))
        most_frequent = next(d for d in supply if appearances.get(d) == top)
        rarest = next(d for d in supply if appearances.get(d) == bottom)
    fleeting = sorted(drive for drive in appearances if appearances[drive] == 1)
    return {'total': len(rows), 'appearances': appearances, 'energy': energy,
            'most_frequent': most_frequent, 'rarest': rarest,
            'fleeting': fleeting}


def _core(m):
    # fixed pins, oracle seeded with row number 1876
    assert m.analyze_drives([('hamlet', 'id', 5), ('hamlet', 'id', 3),
                             ('othello', 'ego', 9)]) == {
        'total': 3, 'appearances': {'id': 2, 'ego': 1},
        'energy': {'id': 8, 'ego': 9},
        'most_frequent': 'id', 'rarest': 'ego', 'fleeting': ['ego']}
    # one row: the only drive is everything at once
    assert m.analyze_drives([('t', 'd', 5)]) == {
        'total': 1, 'appearances': {'d': 1}, 'energy': {'d': 5},
        'most_frequent': 'd', 'rarest': 'd', 'fleeting': ['d']}
    # frequency ties go to the first supplied
    r = m.analyze_drives([('t', 'a', 1), ('t', 'b', 1)])
    assert r['most_frequent'] == 'a' and r['rarest'] == 'a'
    assert r['fleeting'] == ['a', 'b']
    # most frequent is about appearances, not intensity
    r = m.analyze_drives([('t', 'a', 1), ('t', 'a', 1), ('t', 'b', 9)])
    assert r['most_frequent'] == 'a' and r['energy'] == {'a': 2, 'b': 9}
    # frequency ties ignore alphabetical order
    r = m.analyze_drives([('t', 'z', 1), ('u', 'a', 1)])
    assert r['most_frequent'] == 'z' and r['rarest'] == 'z'
    # the rarest tie goes to the first supplied, fleeting sorted
    r = m.analyze_drives([('t', 'c', 4), ('t', 'b', 2), ('t', 'b', 3),
                          ('t', 'a', 1)])
    assert r['appearances'] == {'c': 1, 'b': 2, 'a': 1}
    assert r['rarest'] == 'c' and r['fleeting'] == ['a', 'c']
    # dicts keep first-touch order
    r = m.analyze_drives([('t', 'z', 1), ('t', 'a', 2)])
    assert r['appearances'] == {'z': 1, 'a': 1} and r['energy'] == {'z': 1, 'a': 2}
    assert r['fleeting'] == ['a', 'z']
    # non-ASCII texts and drives follow the same rule
    r = m.analyze_drives([('Üser-9!', 'Ω-1', 9), ('q?7', 'Ω-1', 1)])
    assert r == {'total': 2, 'appearances': {'Ω-1': 2}, 'energy': {'Ω-1': 10},
                 'most_frequent': 'Ω-1', 'rarest': 'Ω-1', 'fleeting': []}
    rng = random.Random(1876)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.analyze_drives(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.analyze_drives, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.analyze_drives, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.analyze_drives, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.analyze_drives, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (text, drive, intensity) triple',
            m.analyze_drives, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.analyze_drives, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.analyze_drives, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TM, m.analyze_drives, [(1, 'b', 1)])
    _raises(ValueError, TM, m.analyze_drives, [('', 'b', 1)])
    _raises(ValueError, TM, m.analyze_drives, [('x' * 17, 'b', 1)])
    _raises(ValueError, DM, m.analyze_drives, [('a', 1, 1)])
    _raises(ValueError, DM, m.analyze_drives, [('a', '', 1)])
    _raises(ValueError, DM, m.analyze_drives, [('a', 'x' * 17, 1)])
    _raises(ValueError, IM, m.analyze_drives, [('a', 'b', '1')])
    _raises(ValueError, IM, m.analyze_drives, [('a', 'b', 0)])
    _raises(ValueError, IM, m.analyze_drives, [('a', 'b', 10)])
    _raises(ValueError, IM, m.analyze_drives, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: text must be a string of 1 to 16 characters',
            m.analyze_drives, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: intensity must be a nonbool integer between 1 and 9',
            m.analyze_drives, [('a', 'b', 1), ('c', 'd', 0)])
    # text is validated before drive, drive before intensity
    _raises(ValueError, TM, m.analyze_drives, [('x' * 17, '', 0)])
    _raises(ValueError, DM, m.analyze_drives, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.analyze_drives, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.analyze_drives((('a', 'b', 1),)) == m.analyze_drives([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.analyze_drives([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.analyze_drives([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.analyze_drives([('a', 'b', 1)] * 60)['total'] == 60
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.analyze_drives([('x' * 16, 'b', 5)])['total'] == 1
    assert m.analyze_drives([('a', 'y' * 16, 5)])['total'] == 1
    assert m.analyze_drives([('a', 'b', 5),
                             ('x' * 16, 'y' * 16, 5)])['total'] == 2
    assert m.analyze_drives([('a', 'b', 9)])['energy'] == {'b': 9}
    # pre-seed pin: fresh accumulators only
    assert m.analyze_drives([('a', 'p', 2), ('b', 'p', 8), ('a', 'q', 5)]) == {
        'total': 3, 'appearances': {'p': 2, 'q': 1}, 'energy': {'p': 10, 'q': 5},
        'most_frequent': 'p', 'rarest': 'q', 'fleeting': ['q']}
    return True


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def _sym(m):
    P = 'rows must be a list or tuple'
    for K in (L, T):
        _raises(TypeError, P, m.analyze_drives, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (text, drive, intensity) triple',
                m.analyze_drives, [K(('a', 'b', 1))])
    _raises(ValueError, TM, m.analyze_drives, [(S('a'), 'b', 1)])
    _raises(ValueError, DM, m.analyze_drives, [('a', S('b'), 1)])
    _raises(ValueError, IM, m.analyze_drives, [('a', 'b', I(1))])
    return True


def battery(m):
    _core(m)
    _late(m)
    _sym(m)
    return True


MUTANTS = [
    ('type(rows) not in (list, tuple)', 'not isinstance(rows, (list, tuple))'),
    ('not 1 <= len(rows) <= 60', 'not 1 <= len(rows) <= 61'),
    ('not 1 <= len(rows) <= 60', 'not 0 <= len(rows) <= 60'),
    ('type(row) not in (list, tuple)', 'not isinstance(row, (list, tuple))'),
    ('len(row) != 3', 'len(row) != 2'),
    ('type(text) is not str', 'not isinstance(text, str)'),
    ('type(drive) is not str', 'not isinstance(drive, str)'),
    ('type(intensity) is not int', 'not isinstance(intensity, int)'),
    ('not 1 <= len(text) <= 16', 'not 1 <= len(text) <= 17'),
    ('not 1 <= len(drive) <= 16', 'not 1 <= len(drive) <= 17'),
    ('not 1 <= intensity <= 9', 'not 1 <= intensity <= 10'),
    ('        appearances[drive] += 1', '        appearances[drive] += 2'),
    ('        energy[drive] += intensity', '        energy[drive] += 1'),
    ('if most_frequent is None or appearances[drive] > appearances[most_frequent]:',
     'if most_frequent is None or appearances[drive] < appearances[most_frequent]:'),
    ('    for drive in appearances:', '    for drive in sorted(appearances):'),
    ('for drive in appearances:\n        if rarest is None',
     'for drive in sorted(appearances):\n        if rarest is None'),
    ('if rarest is None or appearances[drive] < appearances[rarest]:',
     'if rarest is None or appearances[drive] > appearances[rarest]:'),
    ('if appearances[drive] == 1', 'if appearances[drive] == 2'),
    ('    fleeting = sorted(', '    fleeting = list('),
    ("'most_frequent': most_frequent", "'most_frequent': rarest"),
    ("'energy': energy", "'energy': appearances"),
    ("'total': len(rows)", "'total': len(appearances)"),
    ('        text, drive, intensity = row',
     '        drive, text, intensity = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
