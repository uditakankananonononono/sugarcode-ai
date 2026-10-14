import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import dance_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
MV = 'row 1: move must be a string of 1 to 16 characters'
CR = 'row 1: crew must be a string of 1 to 16 characters'
PW = 'row 1: power must be a nonbool integer between 1 and 9'


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
    assert section == ('choreography, technique, injury prevention, '
                       'stage lighting, production readiness.')
    assert mod.SCOPE == 'PARTIAL: level reading over supplied powers'
    assert mod.NOT_CLAIMED == ('choreography', 'technique',
                               'injury prevention', 'stage lighting',
                               'production readiness')


def _expected(rows):
    levels = {}
    crews = {}
    for move, crew, power in rows:
        if power not in levels:
            levels[power] = 0
            crews[power] = {}
        levels[power] += 1
        crews[power][crew] = True
    missing = sorted(p for p in range(1, 10) if p not in levels)
    broadest = None
    for power in levels:
        if broadest is None or len(crews[power]) > len(crews[broadest]):
            broadest = power
    return {'total': len(rows), 'levels': levels,
            'missing': missing, 'broadest': broadest}


def _core(m):
    # fixed pins, oracle seeded with row number 1915
    assert m.read_levels([('m1', 'c1', 9), ('m2', 'c2', 1), ('m3', 'c1', 1),
                          ('m4', 'c3', 9), ('m5', 'c2', 9)]) == {
        'total': 5, 'levels': {9: 3, 1: 2},
        'missing': [2, 3, 4, 5, 6, 7, 8], 'broadest': 9}
    # a single row uses one level once
    assert m.read_levels([('m', 'c', 5)]) == {
        'total': 1, 'levels': {5: 1},
        'missing': [1, 2, 3, 4, 6, 7, 8, 9], 'broadest': 5}
    # every level used means nothing missing
    r = m.read_levels([('m', 'c', p) for p in range(1, 10)])
    assert r['missing'] == []
    # the broadest level counts distinct crews, not rows
    r = m.read_levels([('a', 'x', 2), ('b', 'y', 2), ('c', 'z', 4)])
    assert r['levels'] == {2: 2, 4: 1} and r['broadest'] == 2
    # repeat rows by one crew do not broaden a level
    r = m.read_levels([('a', 'x', 3), ('b', 'y', 7), ('c', 'z', 7)])
    assert r['broadest'] == 7
    # the broadest tie goes to the first used level
    r = m.read_levels([('a', 'x', 4), ('b', 'y', 4), ('c', 'y', 6)])
    assert r['broadest'] == 4
    # dicts keep first-use order
    r = m.read_levels([('a', 'x', 9), ('b', 'y', 1)])
    assert r['levels'] == {9: 1, 1: 1}
    # non-ASCII crews follow the same rule
    r = m.read_levels([('m', 'Üser-9!', 2), ('n', 'q?7', 2), ('o', 'Ω-1', 8)])
    assert r == {'total': 3, 'levels': {2: 2, 8: 1},
                 'missing': [1, 3, 4, 5, 6, 7, 9], 'broadest': 2}
    # pre-seed pin: fresh accumulators only
    assert m.read_levels([('a', 'p', 1), ('b', 'q', 1),
                          ('c', 'p', 1), ('d', 'r', 2)]) == {
        'total': 4, 'levels': {1: 3, 2: 1},
        'missing': [3, 4, 5, 6, 7, 8, 9], 'broadest': 1}
    rng = random.Random(1915)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.read_levels(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.read_levels, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.read_levels, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.read_levels, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.read_levels, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (move, crew, power) triple',
            m.read_levels, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.read_levels, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.read_levels, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, MV, m.read_levels, [(1, 'b', 1)])
    _raises(ValueError, MV, m.read_levels, [('', 'b', 1)])
    _raises(ValueError, MV, m.read_levels, [('x' * 17, 'b', 1)])
    _raises(ValueError, CR, m.read_levels, [('a', 1, 1)])
    _raises(ValueError, CR, m.read_levels, [('a', '', 1)])
    _raises(ValueError, CR, m.read_levels, [('a', 'x' * 17, 1)])
    _raises(ValueError, PW, m.read_levels, [('a', 'b', '1')])
    _raises(ValueError, PW, m.read_levels, [('a', 'b', 0)])
    _raises(ValueError, PW, m.read_levels, [('a', 'b', 10)])
    _raises(ValueError, PW, m.read_levels, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: move must be a string of 1 to 16 characters',
            m.read_levels, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: power must be a nonbool integer between 1 and 9',
            m.read_levels, [('a', 'b', 1), ('c', 'd', 0)])
    # move is validated before crew, crew before power
    _raises(ValueError, MV, m.read_levels, [('x' * 17, '', 0)])
    _raises(ValueError, CR, m.read_levels, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.read_levels, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.read_levels((('a', 'b', 1),)) == m.read_levels([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.read_levels([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.read_levels([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.read_levels([('a', 'b', 1)] * 60)['total'] == 60
    assert m.read_levels([('a', 'b', 9)])['levels'] == {9: 1}
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
        _raises(TypeError, P, m.read_levels, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (move, crew, power) triple',
                m.read_levels, [K(('a', 'b', 1))])
    _raises(ValueError, MV, m.read_levels, [(S('a'), 'b', 1)])
    _raises(ValueError, CR, m.read_levels, [('a', S('b'), 1)])
    _raises(ValueError, PW, m.read_levels, [('a', 'b', I(1))])
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
    ('type(move) is not str', 'not isinstance(move, str)'),
    ('type(crew) is not str', 'not isinstance(crew, str)'),
    ('type(power) is not int', 'not isinstance(power, int)'),
    ('not 1 <= len(move) <= 16', 'not 1 <= len(move) <= 17'),
    ('not 1 <= len(crew) <= 16', 'not 1 <= len(crew) <= 17'),
    ('not 1 <= power <= 9', 'not 1 <= power <= 10'),
    ('        levels[power] += 1', '        levels[power] += 2'),
    ('        crews[power][crew] = True', '        crews[power] = {}'),
    ('missing = sorted(p for p in range(1, 10) if p not in levels)',
     'missing = sorted(p for p in range(1, 9) if p not in levels)'),
    ('if broadest is None or len(crews[power]) > len(crews[broadest]):',
     'if broadest is None or len(crews[power]) < len(crews[broadest]):'),
    ("'levels': levels", "'levels': {}"),
    ("'missing': missing", "'missing': []"),
    ("'broadest': broadest", "'broadest': None"),
    ("'total': len(rows)", "'total': len(levels)"),
    ('        move, crew, power = row',
     '        crew, move, power = row'),
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
    assert mod.read_levels([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.read_levels([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.read_levels([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
