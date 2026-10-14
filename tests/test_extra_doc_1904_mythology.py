import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import mythology as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
HR = 'row 1: hero must be a string of 1 to 16 characters'
MY = 'row 1: myth must be a string of 1 to 16 characters'
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
    assert section == ('mythography, archetypes, comparative mythology, '
                       'cult practice, production readiness.')
    assert mod.SCOPE == 'PARTIAL: hero ranking over supplied powers'
    assert mod.NOT_CLAIMED == ('mythography', 'archetypes',
                               'comparative mythology', 'cult practice',
                               'production readiness')


def _expected(rows):
    floors = {}
    for hero, myth, power in rows:
        if hero not in floors:
            floors[hero] = power
        elif power < floors[hero]:
            floors[hero] = power
    unbeaten = sorted(h for h in floors if floors[h] >= 7)
    fragile = sorted(h for h in floors if floors[h] <= 2)
    sturdiest = None
    for hero in floors:
        if sturdiest is None or floors[hero] > floors[sturdiest]:
            sturdiest = hero
    return {'total': len(rows), 'floors': floors, 'unbeaten': unbeaten,
            'fragile': fragile, 'sturdiest': sturdiest}


def _core(m):
    # fixed pins, oracle seeded with row number 1904
    assert m.rank_heroes([('h1', 'a', 9), ('h1', 'b', 7),
                          ('h2', 'c', 1), ('h2', 'd', 5)]) == {
        'total': 4, 'floors': {'h1': 7, 'h2': 1}, 'unbeaten': ['h1'],
        'fragile': ['h2'], 'sturdiest': 'h1'}
    # one row: its power is the floor
    assert m.rank_heroes([('h', 'm', 5)]) == {
        'total': 1, 'floors': {'h': 5}, 'unbeaten': [],
        'fragile': [], 'sturdiest': 'h'}
    # a floor of exactly 7 is unbeaten, 6 is not
    assert m.rank_heroes([('h', 'a', 7), ('h', 'b', 9)])['unbeaten'] == ['h']
    assert m.rank_heroes([('h', 'a', 6), ('h', 'b', 9)])['unbeaten'] == []
    # a floor of exactly 2 is fragile, 3 is not
    assert m.rank_heroes([('h', 'a', 5), ('h', 'b', 2)])['fragile'] == ['h']
    assert m.rank_heroes([('h', 'a', 5), ('h', 'b', 3)])['fragile'] == []
    # the floor can drop on any later row
    assert m.rank_heroes([('h', 'a', 9), ('h', 'b', 9),
                          ('h', 'c', 1)])['floors'] == {'h': 1}
    # the sturdiest tie goes to the first supplied hero
    r = m.rank_heroes([('a', 'm', 7), ('b', 'm', 7)])
    assert r['unbeaten'] == ['a', 'b'] and r['sturdiest'] == 'a'
    # dicts keep first-touch order
    r = m.rank_heroes([('z', 'm', 1), ('a', 'm', 2)])
    assert r['floors'] == {'z': 1, 'a': 2} and r['fragile'] == ['a', 'z']
    # non-ASCII heroes follow the same rule
    r = m.rank_heroes([('Üser-9!', 'a', 8), ('Üser-9!', 'b', 9), ('q?7', 'c', 2)])
    assert r == {'total': 3, 'floors': {'Üser-9!': 8, 'q?7': 2},
                 'unbeaten': ['Üser-9!'], 'fragile': ['q?7'],
                 'sturdiest': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.rank_heroes([('p', 'a', 8), ('p', 'b', 7), ('q', 'c', 1)]) == {
        'total': 3, 'floors': {'p': 7, 'q': 1}, 'unbeaten': ['p'],
        'fragile': ['q'], 'sturdiest': 'p'}
    rng = random.Random(1904)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.rank_heroes(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.rank_heroes, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.rank_heroes, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.rank_heroes, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.rank_heroes, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (hero, myth, power) triple',
            m.rank_heroes, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.rank_heroes, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.rank_heroes, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, HR, m.rank_heroes, [(1, 'b', 1)])
    _raises(ValueError, HR, m.rank_heroes, [('', 'b', 1)])
    _raises(ValueError, HR, m.rank_heroes, [('x' * 17, 'b', 1)])
    _raises(ValueError, MY, m.rank_heroes, [('a', 1, 1)])
    _raises(ValueError, MY, m.rank_heroes, [('a', '', 1)])
    _raises(ValueError, MY, m.rank_heroes, [('a', 'x' * 17, 1)])
    _raises(ValueError, PW, m.rank_heroes, [('a', 'b', '1')])
    _raises(ValueError, PW, m.rank_heroes, [('a', 'b', 0)])
    _raises(ValueError, PW, m.rank_heroes, [('a', 'b', 10)])
    _raises(ValueError, PW, m.rank_heroes, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: hero must be a string of 1 to 16 characters',
            m.rank_heroes, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: power must be a nonbool integer between 1 and 9',
            m.rank_heroes, [('a', 'b', 1), ('c', 'd', 0)])
    # hero is validated before myth, myth before power
    _raises(ValueError, HR, m.rank_heroes, [('x' * 17, '', 0)])
    _raises(ValueError, MY, m.rank_heroes, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.rank_heroes, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.rank_heroes((('a', 'b', 1),)) == m.rank_heroes([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.rank_heroes([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.rank_heroes([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.rank_heroes([('a', 'b', 1)] * 60)['total'] == 60
    assert m.rank_heroes([('a', 'b', 9)])['floors'] == {'a': 9}
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
        _raises(TypeError, P, m.rank_heroes, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (hero, myth, power) triple',
                m.rank_heroes, [K(('a', 'b', 1))])
    _raises(ValueError, HR, m.rank_heroes, [(S('a'), 'b', 1)])
    _raises(ValueError, MY, m.rank_heroes, [('a', S('b'), 1)])
    _raises(ValueError, PW, m.rank_heroes, [('a', 'b', I(1))])
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
    ('type(hero) is not str', 'not isinstance(hero, str)'),
    ('type(myth) is not str', 'not isinstance(myth, str)'),
    ('type(power) is not int', 'not isinstance(power, int)'),
    ('not 1 <= len(hero) <= 16', 'not 1 <= len(hero) <= 17'),
    ('not 1 <= len(myth) <= 16', 'not 1 <= len(myth) <= 17'),
    ('not 1 <= power <= 9', 'not 1 <= power <= 10'),
    ('        if hero not in floors:', '        if hero in floors:'),
    ('        elif power < floors[hero]:', '        elif power > floors[hero]:'),
    ('if floors[h] >= 7', 'if floors[h] >= 8'),
    ('if floors[h] <= 2', 'if floors[h] <= 1'),
    ('if sturdiest is None or floors[hero] > floors[sturdiest]:',
     'if sturdiest is None or floors[hero] < floors[sturdiest]:'),
    ("'unbeaten': unbeaten", "'unbeaten': fragile"),
    ("'floors': floors", "'floors': {}"),
    ("'total': len(rows)", "'total': len(floors)"),
    ('        hero, myth, power = row',
     '        myth, hero, power = row'),
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
    assert mod.rank_heroes([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.rank_heroes([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.rank_heroes([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
