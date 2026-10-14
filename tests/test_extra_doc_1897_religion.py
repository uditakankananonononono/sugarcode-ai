import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import religion as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TD = 'row 1: tradition must be a string of 1 to 16 characters'
PR = 'row 1: practice must be a string of 1 to 16 characters'
AD = 'row 1: adherents must be a nonbool integer between 1 and 9'


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
    assert section == ('theology, comparative belief, ritual practice, '
                       'census accuracy, production readiness.')
    assert mod.SCOPE == 'PARTIAL: tradition surveying over supplied tallies'
    assert mod.NOT_CLAIMED == ('theology', 'comparative belief',
                               'ritual practice', 'census accuracy',
                               'production readiness')


def _expected(rows):
    totals = {}
    counts = {}
    for tradition, practice, adherents in rows:
        if tradition not in totals:
            totals[tradition] = 0
            counts[tradition] = 0
        totals[tradition] += adherents
        counts[tradition] += 1
    streak_tradition = rows[0][0]
    streak_length = 1
    run_tradition = rows[0][0]
    run_length = 1
    for tradition, practice, adherents in rows[1:]:
        if tradition == run_tradition:
            run_length += 1
        else:
            run_tradition = tradition
            run_length = 1
        if run_length > streak_length:
            streak_tradition = run_tradition
            streak_length = run_length
    widespread = sorted(t for t in counts if counts[t] >= 3)
    devoted = None
    for tradition in totals:
        if devoted is None or totals[tradition] > totals[devoted]:
            devoted = tradition
    return {'total': len(rows), 'totals': totals,
            'streak': {'tradition': streak_tradition, 'length': streak_length},
            'widespread': widespread, 'devoted': devoted}


def _core(m):
    # fixed pins, oracle seeded with row number 1897
    assert m.survey_traditions([('a', 'p', 2), ('a', 'q', 3), ('a', 'r', 1),
                                ('b', 's', 4), ('b', 't', 5)]) == {
        'total': 5, 'totals': {'a': 6, 'b': 9},
        'streak': {'tradition': 'a', 'length': 3},
        'widespread': ['a'], 'devoted': 'b'}
    # a later run of equal length does not take the streak
    r = m.survey_traditions([('a', 'p', 1), ('a', 'q', 1),
                             ('b', 'r', 1), ('b', 's', 1)])
    assert r['streak'] == {'tradition': 'a', 'length': 2}
    # the longest run can start after another tradition
    r = m.survey_traditions([('b', 'p', 1), ('a', 'q', 1),
                             ('a', 'r', 1), ('a', 's', 1)])
    assert r == {'total': 4, 'totals': {'b': 1, 'a': 3},
                 'streak': {'tradition': 'a', 'length': 3},
                 'widespread': ['a'], 'devoted': 'a'}
    # one row: a streak of one
    assert m.survey_traditions([('t', 'p', 5)]) == {
        'total': 1, 'totals': {'t': 5},
        'streak': {'tradition': 't', 'length': 1},
        'widespread': [], 'devoted': 't'}
    # an interrupted run restarts at one
    r = m.survey_traditions([('a', 'p', 1), ('b', 'q', 1), ('a', 'r', 1)])
    assert r['streak'] == {'tradition': 'a', 'length': 1}
    assert r['totals'] == {'a': 2, 'b': 1}
    # three rows is widespread, two is not
    assert m.survey_traditions([('a', 'p', 1), ('a', 'q', 1),
                                ('a', 'r', 1)])['widespread'] == ['a']
    assert m.survey_traditions([('a', 'p', 1), ('a', 'q', 1)])['widespread'] == []
    # the devoted tie goes to the first supplied tradition
    assert m.survey_traditions([('x', 'p', 9), ('y', 'q', 9)])['devoted'] == 'x'
    # dicts keep first-touch order
    r = m.survey_traditions([('z', 'p', 1), ('a', 'q', 2)])
    assert r['totals'] == {'z': 1, 'a': 2}
    # non-ASCII traditions follow the same rule
    r = m.survey_traditions([('Üser-9!', 'p', 9), ('Üser-9!', 'q', 9),
                             ('Üser-9!', 'r', 9), ('q?7', 's', 1)])
    assert r == {'total': 4, 'totals': {'Üser-9!': 27, 'q?7': 1},
                 'streak': {'tradition': 'Üser-9!', 'length': 3},
                 'widespread': ['Üser-9!'], 'devoted': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.survey_traditions([('p', 'a', 3), ('p', 'b', 3),
                                ('q', 'c', 5), ('q', 'd', 5)]) == {
        'total': 4, 'totals': {'p': 6, 'q': 10},
        'streak': {'tradition': 'p', 'length': 2},
        'widespread': [], 'devoted': 'q'}
    rng = random.Random(1897)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.survey_traditions(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.survey_traditions, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.survey_traditions, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.survey_traditions, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.survey_traditions, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (tradition, practice, adherents) triple',
            m.survey_traditions, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.survey_traditions, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.survey_traditions, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TD, m.survey_traditions, [(1, 'b', 1)])
    _raises(ValueError, TD, m.survey_traditions, [('', 'b', 1)])
    _raises(ValueError, TD, m.survey_traditions, [('x' * 17, 'b', 1)])
    _raises(ValueError, PR, m.survey_traditions, [('a', 1, 1)])
    _raises(ValueError, PR, m.survey_traditions, [('a', '', 1)])
    _raises(ValueError, PR, m.survey_traditions, [('a', 'x' * 17, 1)])
    _raises(ValueError, AD, m.survey_traditions, [('a', 'b', '1')])
    _raises(ValueError, AD, m.survey_traditions, [('a', 'b', 0)])
    _raises(ValueError, AD, m.survey_traditions, [('a', 'b', 10)])
    _raises(ValueError, AD, m.survey_traditions, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: tradition must be a string of 1 to 16 characters',
            m.survey_traditions, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: adherents must be a nonbool integer between 1 and 9',
            m.survey_traditions, [('a', 'b', 1), ('c', 'd', 0)])
    # tradition is validated before practice, practice before adherents
    _raises(ValueError, TD, m.survey_traditions, [('x' * 17, '', 0)])
    _raises(ValueError, PR, m.survey_traditions, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.survey_traditions, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.survey_traditions((('a', 'b', 1),)) == m.survey_traditions([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.survey_traditions([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.survey_traditions([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.survey_traditions([('a', 'b', 1)] * 60)['total'] == 60
    assert m.survey_traditions([('a', 'b', 9)])['totals'] == {'a': 9}
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
        _raises(TypeError, P, m.survey_traditions, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (tradition, practice, adherents) triple',
                m.survey_traditions, [K(('a', 'b', 1))])
    _raises(ValueError, TD, m.survey_traditions, [(S('a'), 'b', 1)])
    _raises(ValueError, PR, m.survey_traditions, [('a', S('b'), 1)])
    _raises(ValueError, AD, m.survey_traditions, [('a', 'b', I(1))])
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
    ('type(tradition) is not str', 'not isinstance(tradition, str)'),
    ('type(practice) is not str', 'not isinstance(practice, str)'),
    ('type(adherents) is not int', 'not isinstance(adherents, int)'),
    ('not 1 <= len(tradition) <= 16', 'not 1 <= len(tradition) <= 17'),
    ('not 1 <= len(practice) <= 16', 'not 1 <= len(practice) <= 17'),
    ('not 1 <= adherents <= 9', 'not 1 <= adherents <= 10'),
    ('        totals[tradition] += adherents',
     '        totals[tradition] += 1'),
    ('        counts[tradition] += 1', '        counts[tradition] += 2'),
    ('    streak_tradition = rows[0][0]', '    streak_tradition = rows[0][1]'),
    ('if tradition == run_tradition:', 'if tradition != run_tradition:'),
    ('            run_length = 1', '            run_length = 0'),
    ('if run_length > streak_length:', 'if run_length >= streak_length:'),
    ('if counts[t] >= 3', 'if counts[t] >= 4'),
    ("'streak': {'tradition': streak_tradition, 'length': streak_length}",
     "'streak': {'tradition': streak_tradition, 'length': run_length}"),
    ('if devoted is None or totals[tradition] > totals[devoted]:',
     'if devoted is None or totals[tradition] < totals[devoted]:'),
    ("'totals': totals", "'totals': counts"),
    ("'widespread': widespread", "'widespread': []"),
    ("'total': len(rows)", "'total': len(totals)"),
    ('        tradition, practice, adherents = row',
     '        practice, tradition, adherents = row'),
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
    assert mod.survey_traditions([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.survey_traditions([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.survey_traditions([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
