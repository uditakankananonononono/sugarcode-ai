import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import history_of_religion as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
ER = 'row 1: era must be a string of 1 to 16 characters'
EV = 'row 1: event must be a string of 1 to 16 characters'
SG = 'row 1: significance must be a nonbool integer between 1 and 9'


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
    assert section == ('periodization, historiography, source criticism, '
                       'causation, production readiness.')
    assert mod.SCOPE == 'PARTIAL: era charting over supplied significances'
    assert mod.NOT_CLAIMED == ('periodization', 'historiography',
                               'source criticism', 'causation',
                               'production readiness')


def _expected(rows):
    totals = {}
    counts = {}
    for era, event, significance in rows:
        if era not in totals:
            totals[era] = 0
            counts[era] = 0
        totals[era] += significance
        counts[era] += 1
    averages = {}
    for era in totals:
        averages[era] = totals[era] // counts[era]
    golden = sorted(era for era in averages if averages[era] >= 7)
    dark = sorted(era for era in averages if averages[era] <= 3)
    zenith = None
    for era in averages:
        if zenith is None or averages[era] > averages[zenith]:
            zenith = era
    return {'total': len(rows), 'averages': averages, 'golden': golden,
            'dark': dark, 'zenith': zenith}


def _core(m):
    # fixed pins, oracle seeded with row number 1900
    assert m.chart_eras([('e1', 'a', 9), ('e1', 'b', 5),
                         ('e2', 'c', 2), ('e2', 'd', 2)]) == {
        'total': 4, 'averages': {'e1': 7, 'e2': 2}, 'golden': ['e1'],
        'dark': ['e2'], 'zenith': 'e1'}
    # the average is floored: 13 over 2 rows is 6
    assert m.chart_eras([('e', 'a', 9), ('e', 'b', 4)])['averages'] == {'e': 6}
    # an average of exactly 7 is golden, 6 is not
    assert m.chart_eras([('e', 'a', 9), ('e', 'b', 5)])['golden'] == ['e']
    assert m.chart_eras([('e', 'a', 9), ('e', 'b', 4)])['golden'] == []
    # an average of exactly 3 is dark, 4 is not
    assert m.chart_eras([('e', 'a', 5), ('e', 'b', 1)])['dark'] == ['e']
    assert m.chart_eras([('e', 'a', 5), ('e', 'b', 3)])['dark'] == []
    # one row: its significance is the average
    assert m.chart_eras([('e', 'v', 5)]) == {
        'total': 1, 'averages': {'e': 5}, 'golden': [],
        'dark': [], 'zenith': 'e'}
    # the zenith tie goes to the first supplied era
    r = m.chart_eras([('a', 'v', 7), ('b', 'v', 7)])
    assert r['golden'] == ['a', 'b'] and r['zenith'] == 'a'
    # dicts keep first-touch order
    r = m.chart_eras([('z', 'v', 1), ('a', 'v', 2)])
    assert r['averages'] == {'z': 1, 'a': 2} and r['dark'] == ['a', 'z']
    # non-ASCII eras follow the same rule
    r = m.chart_eras([('Üser-9!', 'a', 9), ('Üser-9!', 'b', 9), ('q?7', 'c', 1)])
    assert r == {'total': 3, 'averages': {'Üser-9!': 9, 'q?7': 1},
                 'golden': ['Üser-9!'], 'dark': ['q?7'],
                 'zenith': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.chart_eras([('p', 'a', 9), ('p', 'b', 6), ('q', 'c', 2)]) == {
        'total': 3, 'averages': {'p': 7, 'q': 2}, 'golden': ['p'],
        'dark': ['q'], 'zenith': 'p'}
    rng = random.Random(1900)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.chart_eras(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.chart_eras, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.chart_eras, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.chart_eras, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.chart_eras, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (era, event, significance) triple',
            m.chart_eras, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.chart_eras, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.chart_eras, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, ER, m.chart_eras, [(1, 'b', 1)])
    _raises(ValueError, ER, m.chart_eras, [('', 'b', 1)])
    _raises(ValueError, ER, m.chart_eras, [('x' * 17, 'b', 1)])
    _raises(ValueError, EV, m.chart_eras, [('a', 1, 1)])
    _raises(ValueError, EV, m.chart_eras, [('a', '', 1)])
    _raises(ValueError, EV, m.chart_eras, [('a', 'x' * 17, 1)])
    _raises(ValueError, SG, m.chart_eras, [('a', 'b', '1')])
    _raises(ValueError, SG, m.chart_eras, [('a', 'b', 0)])
    _raises(ValueError, SG, m.chart_eras, [('a', 'b', 10)])
    _raises(ValueError, SG, m.chart_eras, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: era must be a string of 1 to 16 characters',
            m.chart_eras, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: significance must be a nonbool integer between 1 and 9',
            m.chart_eras, [('a', 'b', 1), ('c', 'd', 0)])
    # era is validated before event, event before significance
    _raises(ValueError, ER, m.chart_eras, [('x' * 17, '', 0)])
    _raises(ValueError, EV, m.chart_eras, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.chart_eras, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.chart_eras((('a', 'b', 1),)) == m.chart_eras([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.chart_eras([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.chart_eras([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.chart_eras([('a', 'b', 1)] * 60)['total'] == 60
    assert m.chart_eras([('a', 'b', 9)])['averages'] == {'a': 9}
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
        _raises(TypeError, P, m.chart_eras, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (era, event, significance) triple',
                m.chart_eras, [K(('a', 'b', 1))])
    _raises(ValueError, ER, m.chart_eras, [(S('a'), 'b', 1)])
    _raises(ValueError, EV, m.chart_eras, [('a', S('b'), 1)])
    _raises(ValueError, SG, m.chart_eras, [('a', 'b', I(1))])
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
    ('type(era) is not str', 'not isinstance(era, str)'),
    ('type(event) is not str', 'not isinstance(event, str)'),
    ('type(significance) is not int', 'not isinstance(significance, int)'),
    ('not 1 <= len(era) <= 16', 'not 1 <= len(era) <= 17'),
    ('not 1 <= len(event) <= 16', 'not 1 <= len(event) <= 17'),
    ('not 1 <= significance <= 9', 'not 1 <= significance <= 10'),
    ('        totals[era] += significance', '        totals[era] += 1'),
    ('        counts[era] += 1', '        counts[era] += 2'),
    ('averages[era] = totals[era] // counts[era]',
     'averages[era] = totals[era] / counts[era]'),
    ('if averages[era] >= 7', 'if averages[era] >= 8'),
    ('if averages[era] <= 3', 'if averages[era] <= 2'),
    ('if zenith is None or averages[era] > averages[zenith]:',
     'if zenith is None or averages[era] < averages[zenith]:'),
    ("'golden': golden", "'golden': dark"),
    ("'averages': averages", "'averages': totals"),
    ("'total': len(rows)", "'total': len(averages)"),
    ('        era, event, significance = row',
     '        event, era, significance = row'),
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
    assert mod.chart_eras([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.chart_eras([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.chart_eras([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
