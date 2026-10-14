import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import sociology_of_religion as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
GP = 'row 1: group must be a string of 1 to 16 characters'
PR = 'row 1: practice must be a string of 1 to 16 characters'
SZ = 'row 1: size must be a nonbool integer between 1 and 9'


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
    assert section == ('ethnography, survey sampling, secularization '
                       'theory, social network analysis, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: group tracking over supplied sizes'
    assert mod.NOT_CLAIMED == ('ethnography', 'survey sampling',
                               'secularization theory',
                               'social network analysis',
                               'production readiness')


def _expected(rows):
    seen = {}
    rises = {}
    falls = {}
    for group, practice, size in rows:
        if group not in seen:
            seen[group] = size
            rises[group] = 0
            falls[group] = 0
            continue
        if size > seen[group]:
            rises[group] += 1
        elif size < seen[group]:
            falls[group] += 1
        seen[group] = size
    rising = sorted(g for g in rises if rises[g] > falls[g])
    falling = sorted(g for g in rises if falls[g] > rises[g])
    steepest = None
    for group in rises:
        if steepest is None or rises[group] > rises[steepest]:
            steepest = group
    return {'total': len(rows), 'rises': rises, 'falls': falls,
            'rising': rising, 'falling': falling, 'steepest': steepest}


def _core(m):
    # fixed pins, oracle seeded with row number 1901
    assert m.track_groups([('g1', 'a', 1), ('g1', 'b', 5), ('g1', 'c', 9),
                           ('g2', 'd', 9), ('g2', 'e', 1)]) == {
        'total': 5, 'rises': {'g1': 2, 'g2': 0}, 'falls': {'g1': 0, 'g2': 1},
        'rising': ['g1'], 'falling': ['g2'], 'steepest': 'g1'}
    # equal sizes are neither a rise nor a fall
    assert m.track_groups([('g', 'a', 5), ('g', 'b', 5)]) == {
        'total': 2, 'rises': {'g': 0}, 'falls': {'g': 0},
        'rising': [], 'falling': [], 'steepest': 'g'}
    # one row: no comparisons yet
    assert m.track_groups([('g', 'p', 5)])['rises'] == {'g': 0}
    # comparisons follow each group's own subsequence, not adjacent rows
    r = m.track_groups([('a', 'p', 1), ('b', 'q', 9), ('a', 'r', 5)])
    assert r['rises'] == {'a': 1, 'b': 0} and r['rising'] == ['a']
    # the steepest tie goes to the first supplied group
    r = m.track_groups([('a', 'p', 1), ('a', 'q', 5),
                        ('b', 'r', 1), ('b', 's', 5)])
    assert r['rising'] == ['a', 'b'] and r['steepest'] == 'a'
    # a group can both rise and fall; the balance decides
    r = m.track_groups([('g', 'a', 5), ('g', 'b', 9), ('g', 'c', 1)])
    assert r['rises'] == {'g': 1} and r['falls'] == {'g': 1}
    assert r['rising'] == [] and r['falling'] == []
    # dicts keep first-touch order
    r = m.track_groups([('z', 'p', 1), ('a', 'q', 2)])
    assert r['rises'] == {'z': 0, 'a': 0}
    # non-ASCII groups follow the same rule
    r = m.track_groups([('Üser-9!', 'a', 1), ('Üser-9!', 'b', 9),
                        ('q?7', 'c', 9), ('q?7', 'd', 1)])
    assert r == {'total': 4, 'rises': {'Üser-9!': 1, 'q?7': 0},
                 'falls': {'Üser-9!': 0, 'q?7': 1}, 'rising': ['Üser-9!'],
                 'falling': ['q?7'], 'steepest': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.track_groups([('p', 'a', 1), ('p', 'b', 3), ('p', 'c', 9),
                           ('q', 'd', 5)]) == {
        'total': 4, 'rises': {'p': 2, 'q': 0}, 'falls': {'p': 0, 'q': 0},
        'rising': ['p'], 'falling': [], 'steepest': 'p'}
    rng = random.Random(1901)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.track_groups(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.track_groups, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.track_groups, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_groups, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_groups, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (group, practice, size) triple',
            m.track_groups, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.track_groups, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.track_groups, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, GP, m.track_groups, [(1, 'b', 1)])
    _raises(ValueError, GP, m.track_groups, [('', 'b', 1)])
    _raises(ValueError, GP, m.track_groups, [('x' * 17, 'b', 1)])
    _raises(ValueError, PR, m.track_groups, [('a', 1, 1)])
    _raises(ValueError, PR, m.track_groups, [('a', '', 1)])
    _raises(ValueError, PR, m.track_groups, [('a', 'x' * 17, 1)])
    _raises(ValueError, SZ, m.track_groups, [('a', 'b', '1')])
    _raises(ValueError, SZ, m.track_groups, [('a', 'b', 0)])
    _raises(ValueError, SZ, m.track_groups, [('a', 'b', 10)])
    _raises(ValueError, SZ, m.track_groups, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: group must be a string of 1 to 16 characters',
            m.track_groups, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: size must be a nonbool integer between 1 and 9',
            m.track_groups, [('a', 'b', 1), ('c', 'd', 0)])
    # group is validated before practice, practice before size
    _raises(ValueError, GP, m.track_groups, [('x' * 17, '', 0)])
    _raises(ValueError, PR, m.track_groups, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.track_groups, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.track_groups((('a', 'b', 1),)) == m.track_groups([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.track_groups([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.track_groups([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.track_groups([('a', 'b', 1)] * 60)['total'] == 60
    assert m.track_groups([('a', 'b', 9)])['rises'] == {'a': 0}
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
        _raises(TypeError, P, m.track_groups, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (group, practice, size) triple',
                m.track_groups, [K(('a', 'b', 1))])
    _raises(ValueError, GP, m.track_groups, [(S('a'), 'b', 1)])
    _raises(ValueError, PR, m.track_groups, [('a', S('b'), 1)])
    _raises(ValueError, SZ, m.track_groups, [('a', 'b', I(1))])
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
    ('type(group) is not str', 'not isinstance(group, str)'),
    ('type(practice) is not str', 'not isinstance(practice, str)'),
    ('type(size) is not int', 'not isinstance(size, int)'),
    ('not 1 <= len(group) <= 16', 'not 1 <= len(group) <= 17'),
    ('not 1 <= len(practice) <= 16', 'not 1 <= len(practice) <= 17'),
    ('not 1 <= size <= 9', 'not 1 <= size <= 10'),
    ('        if size > seen[group]:', '        if size >= seen[group]:'),
    ('        elif size < seen[group]:', '        elif size <= seen[group]:'),
    ('            rises[group] += 1', '            rises[group] += 2'),
    ('            falls[group] += 1', '            falls[group] += 2'),
    ('if rises[g] > falls[g]', 'if rises[g] >= falls[g]'),
    ('if falls[g] > rises[g]', 'if falls[g] >= rises[g]'),
    ('if steepest is None or rises[group] > rises[steepest]:',
     'if steepest is None or rises[group] < rises[steepest]:'),
    ("'rising': rising", "'rising': falling"),
    ("'rises': rises", "'rises': falls"),
    ("'total': len(rows)", "'total': len(rises)"),
    ('        group, practice, size = row',
     '        practice, group, size = row'),
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
    assert mod.track_groups([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.track_groups([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.track_groups([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
