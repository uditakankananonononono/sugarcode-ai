import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import theology as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
DC = 'row 1: doctrine must be a string of 1 to 16 characters'
SC = 'row 1: school must be a string of 1 to 16 characters'
WT = 'row 1: weight must be a nonbool integer between 1 and 9'


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
    assert section == ('systematic theology, exegesis, dogmatics, '
                       'historical criticism, production readiness.')
    assert mod.SCOPE == 'PARTIAL: doctrine weighing over supplied weights'
    assert mod.NOT_CLAIMED == ('systematic theology', 'exegesis', 'dogmatics',
                               'historical criticism',
                               'production readiness')


def _expected(rows):
    first = {}
    last = {}
    for doctrine, school, weight in rows:
        if doctrine not in first:
            first[doctrine] = weight
        last[doctrine] = weight
    drifts = {}
    for doctrine in first:
        drifts[doctrine] = last[doctrine] - first[doctrine]
    hardened = sorted(d for d in drifts if drifts[d] >= 3)
    softened = sorted(d for d in drifts if drifts[d] <= -3)
    volatile = None
    for doctrine in drifts:
        if volatile is None or abs(drifts[doctrine]) > abs(drifts[volatile]):
            volatile = doctrine
    return {'total': len(rows), 'drifts': drifts, 'hardened': hardened,
            'softened': softened, 'volatile': volatile}


def _core(m):
    # fixed pins, oracle seeded with row number 1898
    assert m.weigh_doctrines([('d1', 'a', 3), ('d1', 'b', 9),
                              ('d2', 'c', 9), ('d2', 'd', 3)]) == {
        'total': 4, 'drifts': {'d1': 6, 'd2': -6}, 'hardened': ['d1'],
        'softened': ['d2'], 'volatile': 'd1'}
    # one row: no drift
    assert m.weigh_doctrines([('d', 's', 5)]) == {
        'total': 1, 'drifts': {'d': 0}, 'hardened': [],
        'softened': [], 'volatile': 'd'}
    # a drift of exactly 3 hardens, 2 does not
    assert m.weigh_doctrines([('d', 'a', 1), ('d', 'b', 4)])['hardened'] == ['d']
    assert m.weigh_doctrines([('d', 'a', 1), ('d', 'b', 3)])['hardened'] == []
    # a drift of exactly -3 softens, -2 does not
    assert m.weigh_doctrines([('d', 'a', 5), ('d', 'b', 2)])['softened'] == ['d']
    assert m.weigh_doctrines([('d', 'a', 5), ('d', 'b', 3)])['softened'] == []
    # the volatile tie goes to the first supplied doctrine
    r = m.weigh_doctrines([('a', 's', 1), ('a', 's', 5),
                           ('b', 's', 9), ('b', 's', 5)])
    assert r['drifts'] == {'a': 4, 'b': -4} and r['volatile'] == 'a'
    # middle weights do not move the drift
    r = m.weigh_doctrines([('d', 'a', 2), ('d', 'b', 9), ('d', 'c', 2)])
    assert r['drifts'] == {'d': 0}
    # dicts keep first-touch order
    r = m.weigh_doctrines([('z', 's', 1), ('a', 's', 2)])
    assert r['drifts'] == {'z': 0, 'a': 0}
    # non-ASCII doctrines sort by codepoint
    r = m.weigh_doctrines([('Üser-9!', 'a', 9), ('Üser-9!', 'b', 1),
                           ('q?7', 'c', 5)])
    assert r == {'total': 3, 'drifts': {'Üser-9!': -8, 'q?7': 0},
                 'hardened': [], 'softened': ['Üser-9!'],
                 'volatile': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.weigh_doctrines([('p', 'a', 2), ('p', 'b', 8), ('q', 'c', 5)]) == {
        'total': 3, 'drifts': {'p': 6, 'q': 0}, 'hardened': ['p'],
        'softened': [], 'volatile': 'p'}
    rng = random.Random(1898)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.weigh_doctrines(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_doctrines, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_doctrines, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weigh_doctrines, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weigh_doctrines, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (doctrine, school, weight) triple',
            m.weigh_doctrines, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.weigh_doctrines, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.weigh_doctrines, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, DC, m.weigh_doctrines, [(1, 'b', 1)])
    _raises(ValueError, DC, m.weigh_doctrines, [('', 'b', 1)])
    _raises(ValueError, DC, m.weigh_doctrines, [('x' * 17, 'b', 1)])
    _raises(ValueError, SC, m.weigh_doctrines, [('a', 1, 1)])
    _raises(ValueError, SC, m.weigh_doctrines, [('a', '', 1)])
    _raises(ValueError, SC, m.weigh_doctrines, [('a', 'x' * 17, 1)])
    _raises(ValueError, WT, m.weigh_doctrines, [('a', 'b', '1')])
    _raises(ValueError, WT, m.weigh_doctrines, [('a', 'b', 0)])
    _raises(ValueError, WT, m.weigh_doctrines, [('a', 'b', 10)])
    _raises(ValueError, WT, m.weigh_doctrines, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: doctrine must be a string of 1 to 16 characters',
            m.weigh_doctrines, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: weight must be a nonbool integer between 1 and 9',
            m.weigh_doctrines, [('a', 'b', 1), ('c', 'd', 0)])
    # doctrine is validated before school, school before weight
    _raises(ValueError, DC, m.weigh_doctrines, [('x' * 17, '', 0)])
    _raises(ValueError, SC, m.weigh_doctrines, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_doctrines, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.weigh_doctrines((('a', 'b', 1),)) == m.weigh_doctrines([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.weigh_doctrines([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.weigh_doctrines([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.weigh_doctrines([('a', 'b', 1)] * 60)['total'] == 60
    assert m.weigh_doctrines([('a', 'b', 9)])['drifts'] == {'a': 0}
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
        _raises(TypeError, P, m.weigh_doctrines, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (doctrine, school, weight) triple',
                m.weigh_doctrines, [K(('a', 'b', 1))])
    _raises(ValueError, DC, m.weigh_doctrines, [(S('a'), 'b', 1)])
    _raises(ValueError, SC, m.weigh_doctrines, [('a', S('b'), 1)])
    _raises(ValueError, WT, m.weigh_doctrines, [('a', 'b', I(1))])
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
    ('type(doctrine) is not str', 'not isinstance(doctrine, str)'),
    ('type(school) is not str', 'not isinstance(school, str)'),
    ('type(weight) is not int', 'not isinstance(weight, int)'),
    ('not 1 <= len(doctrine) <= 16', 'not 1 <= len(doctrine) <= 17'),
    ('not 1 <= len(school) <= 16', 'not 1 <= len(school) <= 17'),
    ('not 1 <= weight <= 9', 'not 1 <= weight <= 10'),
    ('        if doctrine not in first:', '        if doctrine in first:'),
    ('drifts[doctrine] = last[doctrine] - first[doctrine]',
     'drifts[doctrine] = first[doctrine] - last[doctrine]'),
    ('if drifts[d] >= 3', 'if drifts[d] >= 4'),
    ('if drifts[d] <= -3', 'if drifts[d] <= -2'),
    ('or abs(drifts[doctrine]) > abs(drifts[volatile]):',
     'or abs(drifts[doctrine]) >= abs(drifts[volatile]):'),
    ('or abs(drifts[doctrine]) > abs(drifts[volatile]):',
     'or abs(drifts[doctrine]) < abs(drifts[volatile]):'),
    ("'hardened': hardened", "'hardened': softened"),
    ("'drifts': drifts", "'drifts': first"),
    ("'total': len(rows)", "'total': len(drifts)"),
    ('        doctrine, school, weight = row',
     '        school, doctrine, weight = row'),
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
    assert mod.weigh_doctrines([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.weigh_doctrines([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.weigh_doctrines([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
