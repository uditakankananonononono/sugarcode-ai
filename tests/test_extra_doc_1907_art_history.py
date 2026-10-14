import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import art_history as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
WK = 'row 1: work must be a string of 1 to 16 characters'
PD = 'row 1: period must be a string of 1 to 16 characters'
MR = 'row 1: merit must be a nonbool integer between 1 and 9'


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
    assert section == ('provenance, connoisseurship, iconography, '
                       'conservation, production readiness.')
    assert mod.SCOPE == 'PARTIAL: period crowning over supplied merits'
    assert mod.NOT_CLAIMED == ('provenance', 'connoisseurship',
                               'iconography', 'conservation',
                               'production readiness')


def _expected(rows):
    tops = {}
    masters = {}
    for work, period, merit in rows:
        if period not in tops or merit > tops[period]:
            tops[period] = merit
            masters[period] = work
    celebrated = sorted(p for p in tops if tops[p] >= 8)
    thin = sorted(p for p in tops if tops[p] <= 3)
    finest = None
    for period in tops:
        if finest is None or tops[period] > tops[finest]:
            finest = period
    return {'total': len(rows), 'masters': masters,
            'celebrated': celebrated, 'thin': thin, 'finest': finest}


def _core(m):
    # fixed pins, oracle seeded with row number 1907
    assert m.crown_periods([('w1', 'rena', 3), ('w2', 'rena', 9),
                            ('w3', 'baro', 2)]) == {
        'total': 3, 'masters': {'rena': 'w2', 'baro': 'w3'},
        'celebrated': ['rena'], 'thin': ['baro'], 'finest': 'rena'}
    # one row: the only work is the masterpiece
    assert m.crown_periods([('w', 'p', 5)]) == {
        'total': 1, 'masters': {'p': 'w'}, 'celebrated': [],
        'thin': [], 'finest': 'p'}
    # a merit tie keeps the first supplied work
    assert m.crown_periods([('w1', 'p', 7), ('w2', 'p', 7)])['masters'] == {'p': 'w1'}
    # a later higher merit replaces the masterpiece
    assert m.crown_periods([('w1', 'p', 5), ('w2', 'p', 8)])['masters'] == {'p': 'w2'}
    # a winning merit of exactly 8 celebrates, 7 does not
    assert m.crown_periods([('w', 'p', 8)])['celebrated'] == ['p']
    assert m.crown_periods([('w', 'p', 7)])['celebrated'] == []
    # a winning merit of exactly 3 is thin, 4 is not
    assert m.crown_periods([('w', 'p', 3)])['thin'] == ['p']
    assert m.crown_periods([('w', 'p', 4)])['thin'] == []
    # the finest tie goes to the first supplied period
    r = m.crown_periods([('a', 'x', 9), ('b', 'y', 9)])
    assert r['celebrated'] == ['x', 'y'] and r['finest'] == 'x'
    # dicts keep first-touch order
    r = m.crown_periods([('w1', 'z', 1), ('w2', 'a', 2)])
    assert r['masters'] == {'z': 'w1', 'a': 'w2'} and r['thin'] == ['a', 'z']
    # non-ASCII works and periods follow the same rule
    r = m.crown_periods([('Ω-1', 'Üser-9!', 9), ('a', 'q?7', 2)])
    assert r == {'total': 2, 'masters': {'Üser-9!': 'Ω-1', 'q?7': 'a'},
                 'celebrated': ['Üser-9!'], 'thin': ['q?7'],
                 'finest': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.crown_periods([('w1', 'p', 4), ('w2', 'p', 8), ('w3', 'q', 2)]) == {
        'total': 3, 'masters': {'p': 'w2', 'q': 'w3'},
        'celebrated': ['p'], 'thin': ['q'], 'finest': 'p'}
    rng = random.Random(1907)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.crown_periods(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.crown_periods, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.crown_periods, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.crown_periods, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.crown_periods, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (work, period, merit) triple',
            m.crown_periods, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.crown_periods, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.crown_periods, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, WK, m.crown_periods, [(1, 'b', 1)])
    _raises(ValueError, WK, m.crown_periods, [('', 'b', 1)])
    _raises(ValueError, WK, m.crown_periods, [('x' * 17, 'b', 1)])
    _raises(ValueError, PD, m.crown_periods, [('a', 1, 1)])
    _raises(ValueError, PD, m.crown_periods, [('a', '', 1)])
    _raises(ValueError, PD, m.crown_periods, [('a', 'x' * 17, 1)])
    _raises(ValueError, MR, m.crown_periods, [('a', 'b', '1')])
    _raises(ValueError, MR, m.crown_periods, [('a', 'b', 0)])
    _raises(ValueError, MR, m.crown_periods, [('a', 'b', 10)])
    _raises(ValueError, MR, m.crown_periods, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: work must be a string of 1 to 16 characters',
            m.crown_periods, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: merit must be a nonbool integer between 1 and 9',
            m.crown_periods, [('a', 'b', 1), ('c', 'd', 0)])
    # work is validated before period, period before merit
    _raises(ValueError, WK, m.crown_periods, [('x' * 17, '', 0)])
    _raises(ValueError, PD, m.crown_periods, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.crown_periods, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.crown_periods((('a', 'b', 1),)) == m.crown_periods([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.crown_periods([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.crown_periods([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.crown_periods([('a', 'b', 1)] * 60)['total'] == 60
    assert m.crown_periods([('a', 'b', 9)])['masters'] == {'b': 'a'}
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
        _raises(TypeError, P, m.crown_periods, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (work, period, merit) triple',
                m.crown_periods, [K(('a', 'b', 1))])
    _raises(ValueError, WK, m.crown_periods, [(S('a'), 'b', 1)])
    _raises(ValueError, PD, m.crown_periods, [('a', S('b'), 1)])
    _raises(ValueError, MR, m.crown_periods, [('a', 'b', I(1))])
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
    ('type(work) is not str', 'not isinstance(work, str)'),
    ('type(period) is not str', 'not isinstance(period, str)'),
    ('type(merit) is not int', 'not isinstance(merit, int)'),
    ('not 1 <= len(work) <= 16', 'not 1 <= len(work) <= 17'),
    ('not 1 <= len(period) <= 16', 'not 1 <= len(period) <= 17'),
    ('not 1 <= merit <= 9', 'not 1 <= merit <= 10'),
    ('        if period not in tops or merit > tops[period]:',
     '        if period not in tops or merit >= tops[period]:'),
    ('        if period not in tops or merit > tops[period]:',
     '        if period not in tops or merit < tops[period]:'),
    ('if tops[p] >= 8', 'if tops[p] >= 9'),
    ('if tops[p] <= 3', 'if tops[p] <= 2'),
    ('if finest is None or tops[period] > tops[finest]:',
     'if finest is None or tops[period] < tops[finest]:'),
    ("'masters': masters", "'masters': tops"),
    ("'celebrated': celebrated", "'celebrated': thin"),
    ("'total': len(rows)", "'total': len(tops)"),
    ('        work, period, merit = row',
     '        period, work, merit = row'),
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
    assert mod.crown_periods([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.crown_periods([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.crown_periods([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
