import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import performance_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
AC = 'row 1: act must be a string of 1 to 16 characters'
TR = 'row 1: troupe must be a string of 1 to 16 characters'
EN = 'row 1: energy must be a nonbool integer between 1 and 9'


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
    assert section == ('acting theory, stagecraft, direction, '
                       'casting, production readiness.')
    assert mod.SCOPE == 'PARTIAL: record breaking over supplied energies'
    assert mod.NOT_CLAIMED == ('acting theory', 'stagecraft', 'direction',
                               'casting', 'production readiness')


def _expected(rows):
    peaks = {}
    breaks = {}
    for act, troupe, energy in rows:
        if troupe not in peaks:
            peaks[troupe] = energy
            breaks[troupe] = 0
        elif energy > peaks[troupe]:
            peaks[troupe] = energy
            breaks[troupe] += 1
    quiet = sorted(t for t in breaks if breaks[t] == 0)
    chaser = None
    for troupe in breaks:
        if chaser is None or breaks[troupe] > breaks[chaser]:
            chaser = troupe
    return {'total': len(rows), 'breaks': breaks,
            'quiet': quiet, 'chaser': chaser}


def _core(m):
    # fixed pins, oracle seeded with row number 1914
    assert m.break_records([('a1', 't1', 3), ('a2', 't1', 5), ('a3', 't1', 5),
                            ('a4', 't2', 7), ('a5', 't1', 9), ('a6', 't2', 2)]) == {
        'total': 6, 'breaks': {'t1': 2, 't2': 0},
        'quiet': ['t2'], 'chaser': 't1'}
    # a first row never counts as a break
    assert m.break_records([('a', 't', 5)]) == {
        'total': 1, 'breaks': {'t': 0}, 'quiet': ['t'], 'chaser': 't'}
    # falling short of the running peak is no break
    assert m.break_records([('a', 't', 9), ('b', 't', 1)])['breaks'] == {'t': 0}
    # equal energy is no break either
    assert m.break_records([('a', 't', 5), ('b', 't', 5)])['quiet'] == ['t']
    # the chaser tie goes to the first supplied troupe
    r = m.break_records([('a', 'x', 1), ('a', 'x', 2),
                         ('b', 'y', 1), ('b', 'y', 2)])
    assert r['breaks'] == {'x': 1, 'y': 1} and r['chaser'] == 'x'
    # dicts keep first-touch order
    r = m.break_records([('z', 'b', 1), ('a', 'a', 2)])
    assert r['breaks'] == {'b': 0, 'a': 0}
    # non-ASCII troupes follow the same rule
    r = m.break_records([('a', 'Üser-9!', 1), ('b', 'Üser-9!', 9),
                         ('c', 'q?7', 4), ('d', 'q?7', 8)])
    assert r == {'total': 4, 'breaks': {'Üser-9!': 1, 'q?7': 1},
                 'quiet': [], 'chaser': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.break_records([('a', 'p', 1), ('b', 'p', 2),
                            ('c', 'p', 3), ('d', 'q', 9)]) == {
        'total': 4, 'breaks': {'p': 2, 'q': 0},
        'quiet': ['q'], 'chaser': 'p'}
    rng = random.Random(1914)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.break_records(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.break_records, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.break_records, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.break_records, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.break_records, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (act, troupe, energy) triple',
            m.break_records, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.break_records, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.break_records, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, AC, m.break_records, [(1, 'b', 1)])
    _raises(ValueError, AC, m.break_records, [('', 'b', 1)])
    _raises(ValueError, AC, m.break_records, [('x' * 17, 'b', 1)])
    _raises(ValueError, TR, m.break_records, [('a', 1, 1)])
    _raises(ValueError, TR, m.break_records, [('a', '', 1)])
    _raises(ValueError, TR, m.break_records, [('a', 'x' * 17, 1)])
    _raises(ValueError, EN, m.break_records, [('a', 'b', '1')])
    _raises(ValueError, EN, m.break_records, [('a', 'b', 0)])
    _raises(ValueError, EN, m.break_records, [('a', 'b', 10)])
    _raises(ValueError, EN, m.break_records, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: act must be a string of 1 to 16 characters',
            m.break_records, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: energy must be a nonbool integer between 1 and 9',
            m.break_records, [('a', 'b', 1), ('c', 'd', 0)])
    # act is validated before troupe, troupe before energy
    _raises(ValueError, AC, m.break_records, [('x' * 17, '', 0)])
    _raises(ValueError, TR, m.break_records, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.break_records, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.break_records((('a', 'b', 1),)) == m.break_records([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.break_records([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.break_records([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.break_records([('a', 'b', 1)] * 60)['total'] == 60
    assert m.break_records([('a', 'b', 9)])['breaks'] == {'b': 0}
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
        _raises(TypeError, P, m.break_records, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (act, troupe, energy) triple',
                m.break_records, [K(('a', 'b', 1))])
    _raises(ValueError, AC, m.break_records, [(S('a'), 'b', 1)])
    _raises(ValueError, TR, m.break_records, [('a', S('b'), 1)])
    _raises(ValueError, EN, m.break_records, [('a', 'b', I(1))])
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
    ('type(act) is not str', 'not isinstance(act, str)'),
    ('type(troupe) is not str', 'not isinstance(troupe, str)'),
    ('type(energy) is not int', 'not isinstance(energy, int)'),
    ('not 1 <= len(act) <= 16', 'not 1 <= len(act) <= 17'),
    ('not 1 <= len(troupe) <= 16', 'not 1 <= len(troupe) <= 17'),
    ('not 1 <= energy <= 9', 'not 1 <= energy <= 10'),
    ('        elif energy > peaks[troupe]:', '        elif energy < peaks[troupe]:'),
    ('        elif energy > peaks[troupe]:', '        elif energy >= peaks[troupe]:'),
    ('            breaks[troupe] += 1', '            breaks[troupe] += 2'),
    ('if breaks[t] == 0', 'if breaks[t] == 1'),
    ('if chaser is None or breaks[troupe] > breaks[chaser]:',
     'if chaser is None or breaks[troupe] < breaks[chaser]:'),
    ("'breaks': breaks", "'breaks': peaks"),
    ("'quiet': quiet", "'quiet': []"),
    ("'chaser': chaser", "'chaser': None"),
    ("'total': len(rows)", "'total': len(breaks)"),
    ('        act, troupe, energy = row',
     '        troupe, act, energy = row'),
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
    assert mod.break_records([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.break_records([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.break_records([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
