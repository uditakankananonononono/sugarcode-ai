import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import music_generation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TR = 'row 1: track must be a string of 1 to 16 characters'
CO = 'row 1: composer must be a string of 1 to 16 characters'
LE = 'row 1: level must be a nonbool integer between 1 and 9'


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
    assert section == ('melody quality, harmony modeling, '
                       'arrangement depth, mastering chain, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: level variation over supplied rows'
    assert mod.NOT_CLAIMED == ('melody quality', 'harmony modeling',
                               'arrangement depth', 'mastering chain',
                               'production readiness')


def _expected(rows):
    seqs = {}
    for track, composer, level in rows:
        if composer not in seqs:
            seqs[composer] = []
        seqs[composer].append(level)
    variation = {}
    for composer in seqs:
        seq = seqs[composer]
        total = 0
        for k in range(1, len(seq)):
            total += abs(seq[k] - seq[k - 1])
        variation[composer] = total
    flat = sorted(c for c in variation if variation[c] == 0)
    roughest = None
    for composer in variation:
        if roughest is None or variation[composer] > variation[roughest]:
            roughest = composer
    return {'total': len(rows), 'variation': variation,
            'flat': flat, 'roughest': roughest}


def _core(m):
    # fixed pins, oracle seeded with row number 1931
    assert m.track_variation([('t', 'c1', 2), ('t', 'c1', 5), ('t', 'c1', 3),
                              ('t', 'c2', 4), ('t', 'c2', 4)]) == {
        'total': 5, 'variation': {'c1': 5, 'c2': 0},
        'flat': ['c2'], 'roughest': 'c1'}
    # a single row has zero variation
    assert m.track_variation([('t', 'c', 7)]) == {
        'total': 1, 'variation': {'c': 0}, 'flat': ['c'], 'roughest': 'c'}
    # a full jump is 8
    assert m.track_variation([('t', 'x', 1), ('t', 'x', 9)])['variation'] == {'x': 8}
    # a sawtooth counts both legs
    assert m.track_variation([('t', 'x', 9), ('t', 'x', 1), ('t', 'x', 9)])['variation'] == {'x': 16}
    # the roughest tie goes to the first supplied composer
    r = m.track_variation([('t', 'Üser-9!', 1), ('t', 'q?7', 9),
                           ('t', 'Üser-9!', 9), ('t', 'q?7', 1)])
    assert r == {'total': 4, 'variation': {'Üser-9!': 8, 'q?7': 8},
                 'flat': [], 'roughest': 'Üser-9!'}
    # dicts keep first-touch order
    r = m.track_variation([('z', 'b', 7), ('a', 'a', 2)])
    assert r['variation'] == {'b': 0, 'a': 0}
    assert r['flat'] == ['a', 'b'] and r['roughest'] == 'b'
    # any movement beats a flat composer
    r = m.track_variation([('t', 'p', 1), ('t', 'q', 1), ('t', 'q', 2)])
    assert r['variation'] == {'p': 0, 'q': 1}
    assert r['flat'] == ['p'] and r['roughest'] == 'q'
    # pre-seed pin: fresh accumulators only
    assert m.track_variation([('t', 'a', 1), ('t', 'a', 1),
                              ('t', 'b', 3), ('t', 'b', 5)]) == {
        'total': 4, 'variation': {'a': 0, 'b': 2},
        'flat': ['a'], 'roughest': 'b'}
    rng = random.Random(1931)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.track_variation(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.track_variation, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.track_variation, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_variation, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_variation, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (track, composer, level) triple',
            m.track_variation, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.track_variation, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.track_variation, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TR, m.track_variation, [(1, 'b', 1)])
    _raises(ValueError, TR, m.track_variation, [('', 'b', 1)])
    _raises(ValueError, TR, m.track_variation, [('x' * 17, 'b', 1)])
    _raises(ValueError, CO, m.track_variation, [('a', 1, 1)])
    _raises(ValueError, CO, m.track_variation, [('a', '', 1)])
    _raises(ValueError, CO, m.track_variation, [('a', 'x' * 17, 1)])
    _raises(ValueError, LE, m.track_variation, [('a', 'b', '1')])
    _raises(ValueError, LE, m.track_variation, [('a', 'b', 0)])
    _raises(ValueError, LE, m.track_variation, [('a', 'b', 10)])
    _raises(ValueError, LE, m.track_variation, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: track must be a string of 1 to 16 characters',
            m.track_variation, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: level must be a nonbool integer between 1 and 9',
            m.track_variation, [('a', 'b', 1), ('c', 'd', 0)])
    # track is validated before composer, composer before level
    _raises(ValueError, TR, m.track_variation, [('x' * 17, '', 0)])
    _raises(ValueError, CO, m.track_variation, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.track_variation, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.track_variation((('a', 'b', 1),)) == m.track_variation([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.track_variation([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.track_variation([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.track_variation([('a', 'b', 1)] * 60)['total'] == 60
    assert m.track_variation([('a', 'b', 9)])['variation'] == {'b': 0}
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
        _raises(TypeError, P, m.track_variation, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (track, composer, level) triple',
                m.track_variation, [K(('a', 'b', 1))])
    _raises(ValueError, TR, m.track_variation, [(S('a'), 'b', 1)])
    _raises(ValueError, CO, m.track_variation, [('a', S('b'), 1)])
    _raises(ValueError, LE, m.track_variation, [('a', 'b', I(1))])
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
    ('type(track) is not str', 'not isinstance(track, str)'),
    ('type(composer) is not str', 'not isinstance(composer, str)'),
    ('type(level) is not int', 'not isinstance(level, int)'),
    ('not 1 <= len(track) <= 16', 'not 1 <= len(track) <= 17'),
    ('not 1 <= len(composer) <= 16', 'not 1 <= len(composer) <= 17'),
    ('not 1 <= level <= 9', 'not 1 <= level <= 10'),
    ('        seqs[composer].append(level)', '        seqs[composer].append(1)'),
    ('            total += abs(seq[k] - seq[k - 1])',
     '            total += abs(seq[k] + seq[k - 1])'),
    ('            total += abs(seq[k] - seq[k - 1])',
     '            total += seq[k] - seq[k - 1]'),
    ('variation[c] == 0', 'variation[c] != 0'),
    ('if roughest is None or variation[composer] > variation[roughest]:',
     'if roughest is None or variation[composer] < variation[roughest]:'),
    ("'variation': variation", "'variation': {}"),
    ("'flat': flat", "'flat': []"),
    ("'roughest': roughest", "'roughest': None"),
    ("'total': len(rows)", "'total': len(variation)"),
    ('        track, composer, level = row',
     '        composer, track, level = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True


def test_gap_pin_exact_cap_acceptance():
    # gap sweep: exact-cap 16-char labels accepted in each label
    # position, and on a late row
    assert mod.track_variation([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.track_variation([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.track_variation([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
