import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ritual_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
RT = 'row 1: rite must be a string of 1 to 16 characters'
OF = 'row 1: officiant must be a string of 1 to 16 characters'
SL = 'row 1: solemnity must be a nonbool integer between 1 and 9'


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
    assert section == ('liturgy, ritual efficacy, sacred time, '
                       'initiation rites, production readiness.')
    assert mod.SCOPE == 'PARTIAL: rite weighing over supplied solemnities'
    assert mod.NOT_CLAIMED == ('liturgy', 'ritual efficacy', 'sacred time',
                               'initiation rites', 'production readiness')


def _expected(rows):
    odds = {}
    evens = {}
    for rite, officiant, solemnity in rows:
        if rite not in odds:
            odds[rite] = 0
            evens[rite] = 0
        if solemnity % 2 == 1:
            odds[rite] += 1
        else:
            evens[rite] += 1
    odd_leaning = sorted(r for r in odds if odds[r] > evens[r])
    even_leaning = sorted(r for r in odds if evens[r] > odds[r])
    oddest = None
    if odds:
        top = max(odds.values())
        supply = list(dict.fromkeys(r for r, _o, _s in rows))
        oddest = next(r for r in supply if odds.get(r) == top)
    return {'total': len(rows), 'odds': odds, 'evens': evens,
            'odd_leaning': odd_leaning, 'even_leaning': even_leaning,
            'oddest': oddest}


def _core(m):
    # fixed pins, oracle seeded with row number 1906
    assert m.weigh_rites([('r1', 'a', 1), ('r1', 'b', 2), ('r1', 'c', 3),
                          ('r2', 'd', 2), ('r2', 'e', 4)]) == {
        'total': 5, 'odds': {'r1': 2, 'r2': 0}, 'evens': {'r1': 1, 'r2': 2},
        'odd_leaning': ['r1'], 'even_leaning': ['r2'], 'oddest': 'r1'}
    # one odd row leans odd
    assert m.weigh_rites([('r', 'o', 5)]) == {
        'total': 1, 'odds': {'r': 1}, 'evens': {'r': 0},
        'odd_leaning': ['r'], 'even_leaning': [], 'oddest': 'r'}
    # equal counts lean neither way
    r = m.weigh_rites([('r', 'a', 1), ('r', 'b', 2)])
    assert r['odd_leaning'] == [] and r['even_leaning'] == []
    # an oddest tie ignores alphabetical order
    r = m.weigh_rites([('z', 'o', 1), ('a', 'o', 3)])
    assert r['oddest'] == 'z'
    # the oddest tie goes to the first supplied rite
    r = m.weigh_rites([('a', 'o', 1), ('b', 'o', 3)])
    assert r['odd_leaning'] == ['a', 'b'] and r['oddest'] == 'a'
    # dicts keep first-touch order
    r = m.weigh_rites([('z', 'o', 1), ('a', 'o', 2)])
    assert r['odds'] == {'z': 1, 'a': 0} and r['evens'] == {'z': 0, 'a': 1}
    # non-ASCII rites follow the same rule
    r = m.weigh_rites([('Üser-9!', 'a', 9), ('Üser-9!', 'b', 7), ('q?7', 'c', 2)])
    assert r == {'total': 3, 'odds': {'Üser-9!': 2, 'q?7': 0},
                 'evens': {'Üser-9!': 0, 'q?7': 1},
                 'odd_leaning': ['Üser-9!'], 'even_leaning': ['q?7'],
                 'oddest': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.weigh_rites([('p', 'a', 1), ('p', 'b', 3), ('p', 'c', 2),
                          ('q', 'd', 8)]) == {
        'total': 4, 'odds': {'p': 2, 'q': 0}, 'evens': {'p': 1, 'q': 1},
        'odd_leaning': ['p'], 'even_leaning': ['q'], 'oddest': 'p'}
    rng = random.Random(1906)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.weigh_rites(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_rites, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_rites, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weigh_rites, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weigh_rites, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (rite, officiant, solemnity) triple',
            m.weigh_rites, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.weigh_rites, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.weigh_rites, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, RT, m.weigh_rites, [(1, 'b', 1)])
    _raises(ValueError, RT, m.weigh_rites, [('', 'b', 1)])
    _raises(ValueError, RT, m.weigh_rites, [('x' * 17, 'b', 1)])
    _raises(ValueError, OF, m.weigh_rites, [('a', 1, 1)])
    _raises(ValueError, OF, m.weigh_rites, [('a', '', 1)])
    _raises(ValueError, OF, m.weigh_rites, [('a', 'x' * 17, 1)])
    _raises(ValueError, SL, m.weigh_rites, [('a', 'b', '1')])
    _raises(ValueError, SL, m.weigh_rites, [('a', 'b', 0)])
    _raises(ValueError, SL, m.weigh_rites, [('a', 'b', 10)])
    _raises(ValueError, SL, m.weigh_rites, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: rite must be a string of 1 to 16 characters',
            m.weigh_rites, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: solemnity must be a nonbool integer between 1 and 9',
            m.weigh_rites, [('a', 'b', 1), ('c', 'd', 0)])
    # rite is validated before officiant, officiant before solemnity
    _raises(ValueError, RT, m.weigh_rites, [('x' * 17, '', 0)])
    _raises(ValueError, OF, m.weigh_rites, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_rites, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.weigh_rites((('a', 'b', 1),)) == m.weigh_rites([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.weigh_rites([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.weigh_rites([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.weigh_rites([('a', 'b', 1)] * 60)['total'] == 60
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.weigh_rites([('x' * 16, 'b', 5)])['total'] == 1
    assert m.weigh_rites([('a', 'y' * 16, 5)])['total'] == 1
    assert m.weigh_rites([('a', 'b', 5),
                          ('x' * 16, 'y' * 16, 5)])['total'] == 2
    assert m.weigh_rites([('a', 'b', 9)])['odds'] == {'a': 1}
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
        _raises(TypeError, P, m.weigh_rites, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (rite, officiant, solemnity) triple',
                m.weigh_rites, [K(('a', 'b', 1))])
    _raises(ValueError, RT, m.weigh_rites, [(S('a'), 'b', 1)])
    _raises(ValueError, OF, m.weigh_rites, [('a', S('b'), 1)])
    _raises(ValueError, SL, m.weigh_rites, [('a', 'b', I(1))])
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
    ('type(rite) is not str', 'not isinstance(rite, str)'),
    ('type(officiant) is not str', 'not isinstance(officiant, str)'),
    ('type(solemnity) is not int', 'not isinstance(solemnity, int)'),
    ('not 1 <= len(rite) <= 16', 'not 1 <= len(rite) <= 17'),
    ('not 1 <= len(officiant) <= 16', 'not 1 <= len(officiant) <= 17'),
    ('not 1 <= solemnity <= 9', 'not 1 <= solemnity <= 10'),
    ('        if solemnity % 2 == 1:', '        if solemnity % 2 == 0:'),
    ('            odds[rite] += 1', '            odds[rite] += 2'),
    ('            evens[rite] += 1', '            evens[rite] += 2'),
    ('if odds[r] > evens[r]', 'if odds[r] >= evens[r]'),
    ('if evens[r] > odds[r]', 'if evens[r] >= odds[r]'),
    ('if oddest is None or odds[rite] > odds[oddest]:',
     'if oddest is None or odds[rite] < odds[oddest]:'),
    ('    for rite in odds:', '    for rite in sorted(odds):'),
    ("'odd_leaning': odd_leaning", "'odd_leaning': even_leaning"),
    ("'odds': odds", "'odds': evens"),
    ("'total': len(rows)", "'total': len(odds)"),
    ('        rite, officiant, solemnity = row',
     '        officiant, rite, solemnity = row'),
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
    assert mod.weigh_rites([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.weigh_rites([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.weigh_rites([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
