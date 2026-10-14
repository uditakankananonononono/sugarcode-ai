import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import psychology_of_religion as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SB = 'row 1: subject must be a string of 1 to 16 characters'
EX = 'row 1: experience must be a string of 1 to 16 characters'
IN = 'row 1: intensity must be a nonbool integer between 1 and 9'


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
    assert section == ('clinical diagnosis, mystical experience, '
                       'attachment theory, measurement validity, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: subject probing over supplied intensities'
    assert mod.NOT_CLAIMED == ('clinical diagnosis', 'mystical experience',
                               'attachment theory',
                               'measurement validity',
                               'production readiness')


def _expected(rows):
    marks = {}
    counts = {}
    for subject, experience, intensity in rows:
        if subject not in marks:
            marks[subject] = {}
            counts[subject] = 0
        marks[subject][intensity] = True
        counts[subject] += 1
    gaps = {}
    for subject in marks:
        vals = sorted(marks[subject], reverse=True)
        if len(vals) >= 2:
            gaps[subject] = vals[0] - vals[1]
        else:
            gaps[subject] = 0
    spiked = sorted(s for s in gaps if gaps[s] >= 5)
    level = sorted(s for s in gaps if counts[s] >= 2 and gaps[s] <= 1)
    sharpest = None
    for subject in gaps:
        if sharpest is None or gaps[subject] > gaps[sharpest]:
            sharpest = subject
    return {'total': len(rows), 'gaps': gaps, 'spiked': spiked,
            'level': level, 'sharpest': sharpest}


def _core(m):
    # fixed pins, oracle seeded with row number 1902
    assert m.probe_subjects([('s1', 'a', 1), ('s1', 'b', 9),
                             ('s2', 'c', 5), ('s2', 'd', 6)]) == {
        'total': 4, 'gaps': {'s1': 8, 's2': 1}, 'spiked': ['s1'],
        'level': ['s2'], 'sharpest': 's1'}
    # one row: no second distinct intensity, gap 0
    assert m.probe_subjects([('s', 'e', 5)]) == {
        'total': 1, 'gaps': {'s': 0}, 'spiked': [],
        'level': [], 'sharpest': 's'}
    # a gap of exactly 5 spikes, 4 does not
    assert m.probe_subjects([('s', 'a', 9), ('s', 'b', 4)])['spiked'] == ['s']
    assert m.probe_subjects([('s', 'a', 9), ('s', 'b', 5)])['spiked'] == []
    # a gap of at most 1 over 2+ rows is level
    assert m.probe_subjects([('s', 'a', 3), ('s', 'b', 3)])['level'] == ['s']
    assert m.probe_subjects([('s', 'a', 5), ('s', 'b', 6)])['level'] == ['s']
    # one row is never level
    assert m.probe_subjects([('s', 'a', 5)])['level'] == []
    # repeated intensities do not change the distinct set
    assert m.probe_subjects([('s', 'a', 5), ('s', 'b', 5),
                             ('s', 'c', 5)])['gaps'] == {'s': 0}
    # the sharpest tie goes to the first supplied subject
    r = m.probe_subjects([('a', 'e', 1), ('a', 'e', 9),
                          ('b', 'e', 9), ('b', 'e', 1)])
    assert r['gaps'] == {'a': 8, 'b': 8} and r['sharpest'] == 'a'
    # dicts keep first-touch order
    r = m.probe_subjects([('z', 'e', 1), ('a', 'e', 2)])
    assert r['gaps'] == {'z': 0, 'a': 0}
    # non-ASCII subjects follow the same rule
    r = m.probe_subjects([('Üser-9!', 'a', 9), ('Üser-9!', 'b', 1),
                          ('q?7', 'c', 5), ('q?7', 'd', 5)])
    assert r == {'total': 4, 'gaps': {'Üser-9!': 8, 'q?7': 0},
                 'spiked': ['Üser-9!'], 'level': ['q?7'],
                 'sharpest': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.probe_subjects([('p', 'a', 2), ('p', 'b', 9),
                             ('q', 'c', 4), ('q', 'd', 4)]) == {
        'total': 4, 'gaps': {'p': 7, 'q': 0}, 'spiked': ['p'],
        'level': ['q'], 'sharpest': 'p'}
    rng = random.Random(1902)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.probe_subjects(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.probe_subjects, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.probe_subjects, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.probe_subjects, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.probe_subjects, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (subject, experience, intensity) triple',
            m.probe_subjects, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.probe_subjects, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.probe_subjects, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SB, m.probe_subjects, [(1, 'b', 1)])
    _raises(ValueError, SB, m.probe_subjects, [('', 'b', 1)])
    _raises(ValueError, SB, m.probe_subjects, [('x' * 17, 'b', 1)])
    _raises(ValueError, EX, m.probe_subjects, [('a', 1, 1)])
    _raises(ValueError, EX, m.probe_subjects, [('a', '', 1)])
    _raises(ValueError, EX, m.probe_subjects, [('a', 'x' * 17, 1)])
    _raises(ValueError, IN, m.probe_subjects, [('a', 'b', '1')])
    _raises(ValueError, IN, m.probe_subjects, [('a', 'b', 0)])
    _raises(ValueError, IN, m.probe_subjects, [('a', 'b', 10)])
    _raises(ValueError, IN, m.probe_subjects, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: subject must be a string of 1 to 16 characters',
            m.probe_subjects, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: intensity must be a nonbool integer between 1 and 9',
            m.probe_subjects, [('a', 'b', 1), ('c', 'd', 0)])
    # subject is validated before experience, experience before intensity
    _raises(ValueError, SB, m.probe_subjects, [('x' * 17, '', 0)])
    _raises(ValueError, EX, m.probe_subjects, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.probe_subjects, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.probe_subjects((('a', 'b', 1),)) == m.probe_subjects([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.probe_subjects([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.probe_subjects([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.probe_subjects([('a', 'b', 1)] * 60)['total'] == 60
    assert m.probe_subjects([('a', 'b', 9)])['gaps'] == {'a': 0}
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
        _raises(TypeError, P, m.probe_subjects, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (subject, experience, intensity) triple',
                m.probe_subjects, [K(('a', 'b', 1))])
    _raises(ValueError, SB, m.probe_subjects, [(S('a'), 'b', 1)])
    _raises(ValueError, EX, m.probe_subjects, [('a', S('b'), 1)])
    _raises(ValueError, IN, m.probe_subjects, [('a', 'b', I(1))])
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
    ('type(subject) is not str', 'not isinstance(subject, str)'),
    ('type(experience) is not str', 'not isinstance(experience, str)'),
    ('type(intensity) is not int', 'not isinstance(intensity, int)'),
    ('not 1 <= len(subject) <= 16', 'not 1 <= len(subject) <= 17'),
    ('not 1 <= len(experience) <= 16', 'not 1 <= len(experience) <= 17'),
    ('not 1 <= intensity <= 9', 'not 1 <= intensity <= 10'),
    ('        counts[subject] += 1', '        counts[subject] += 2'),
    ('gaps[subject] = vals[0] - vals[1]',
     'gaps[subject] = vals[1] - vals[0]'),
    ('if gaps[s] >= 5', 'if gaps[s] >= 6'),
    ('if counts[s] >= 2 and gaps[s] <= 1',
     'if counts[s] >= 2 and gaps[s] <= 0'),
    ('if counts[s] >= 2 and gaps[s] <= 1',
     'if counts[s] >= 3 and gaps[s] <= 1'),
    ('if sharpest is None or gaps[subject] > gaps[sharpest]:',
     'if sharpest is None or gaps[subject] < gaps[sharpest]:'),
    ("'spiked': spiked", "'spiked': level"),
    ("'gaps': gaps", "'gaps': counts"),
    ("'total': len(rows)", "'total': len(gaps)"),
    ('        subject, experience, intensity = row',
     '        experience, subject, intensity = row'),
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
    assert mod.probe_subjects([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.probe_subjects([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.probe_subjects([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
