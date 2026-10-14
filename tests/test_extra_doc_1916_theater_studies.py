import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import theater_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PL = 'row 1: play must be a string of 1 to 16 characters'
HO = 'row 1: house must be a string of 1 to 16 characters'
SE = 'row 1: seats must be a nonbool integer between 1 and 9'


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
    assert section == ('dramaturgy, set design, ticketing, '
                       'casting, production readiness.')
    assert mod.SCOPE == 'PARTIAL: peak staging over supplied seats'
    assert mod.NOT_CLAIMED == ('dramaturgy', 'set design', 'ticketing',
                               'casting', 'production readiness')


def _expected(rows):
    peaks = {}
    peak_rows = {}
    last_rows = {}
    for pos, (play, house, seats) in enumerate(rows, 1):
        if house not in peaks:
            peaks[house] = seats
            peak_rows[house] = pos
        elif seats > peaks[house]:
            peaks[house] = seats
            peak_rows[house] = pos
        last_rows[house] = pos
    earliest = None
    for house in peak_rows:
        if earliest is None or peak_rows[house] < peak_rows[earliest]:
            earliest = house
    closers = sorted(h for h in peak_rows if peak_rows[h] == last_rows[h])
    return {'total': len(rows), 'peak_rows': peak_rows,
            'earliest': earliest, 'closers': closers}


def _core(m):
    # fixed pins, oracle seeded with row number 1916
    assert m.stage_peaks([('p1', 'h1', 3), ('p2', 'h2', 9), ('p3', 'h1', 9),
                          ('p4', 'h2', 4), ('p5', 'h1', 5)]) == {
        'total': 5, 'peak_rows': {'h1': 3, 'h2': 2},
        'earliest': 'h2', 'closers': []}
    # a lone row is peak and close at once
    assert m.stage_peaks([('p', 'h', 5)]) == {
        'total': 1, 'peak_rows': {'h': 1}, 'earliest': 'h', 'closers': ['h']}
    # matching the peak later does not move the peak row
    r = m.stage_peaks([('a', 'x', 9), ('b', 'x', 9)])
    assert r['peak_rows'] == {'x': 1} and r['closers'] == []
    # every house can close at once
    r = m.stage_peaks([('a', 'x', 1), ('b', 'y', 2), ('c', 'x', 9)])
    assert r == {'total': 3, 'peak_rows': {'x': 3, 'y': 2},
                 'earliest': 'y', 'closers': ['x', 'y']}
    # the earliest tie is really a row comparison, not supply order
    assert m.stage_peaks([('a', 'x', 9), ('b', 'y', 9)])['earliest'] == 'x'
    # dicts keep first-touch order
    r = m.stage_peaks([('z', 'b', 1), ('a', 'a', 2)])
    assert r['peak_rows'] == {'b': 1, 'a': 2}
    # non-ASCII houses follow the same rule
    r = m.stage_peaks([('p', 'Üser-9!', 1), ('q', 'q?7', 9), ('r', 'Üser-9!', 9)])
    assert r == {'total': 3, 'peak_rows': {'Üser-9!': 3, 'q?7': 2},
                 'earliest': 'q?7', 'closers': ['q?7', 'Üser-9!']}
    # pre-seed pin: fresh accumulators only
    assert m.stage_peaks([('a', 'p', 1), ('b', 'q', 2),
                          ('c', 'p', 8), ('d', 'q', 3)]) == {
        'total': 4, 'peak_rows': {'p': 3, 'q': 4},
        'earliest': 'p', 'closers': ['p', 'q']}
    rng = random.Random(1916)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.stage_peaks(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.stage_peaks, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.stage_peaks, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.stage_peaks, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.stage_peaks, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (play, house, seats) triple',
            m.stage_peaks, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.stage_peaks, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.stage_peaks, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PL, m.stage_peaks, [(1, 'b', 1)])
    _raises(ValueError, PL, m.stage_peaks, [('', 'b', 1)])
    _raises(ValueError, PL, m.stage_peaks, [('x' * 17, 'b', 1)])
    _raises(ValueError, HO, m.stage_peaks, [('a', 1, 1)])
    _raises(ValueError, HO, m.stage_peaks, [('a', '', 1)])
    _raises(ValueError, HO, m.stage_peaks, [('a', 'x' * 17, 1)])
    _raises(ValueError, SE, m.stage_peaks, [('a', 'b', '1')])
    _raises(ValueError, SE, m.stage_peaks, [('a', 'b', 0)])
    _raises(ValueError, SE, m.stage_peaks, [('a', 'b', 10)])
    _raises(ValueError, SE, m.stage_peaks, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: play must be a string of 1 to 16 characters',
            m.stage_peaks, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: seats must be a nonbool integer between 1 and 9',
            m.stage_peaks, [('a', 'b', 1), ('c', 'd', 0)])
    # play is validated before house, house before seats
    _raises(ValueError, PL, m.stage_peaks, [('x' * 17, '', 0)])
    _raises(ValueError, HO, m.stage_peaks, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.stage_peaks, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.stage_peaks((('a', 'b', 1),)) == m.stage_peaks([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.stage_peaks([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.stage_peaks([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.stage_peaks([('a', 'b', 1)] * 60)['total'] == 60
    assert m.stage_peaks([('a', 'b', 9)])['peak_rows'] == {'b': 1}
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
        _raises(TypeError, P, m.stage_peaks, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (play, house, seats) triple',
                m.stage_peaks, [K(('a', 'b', 1))])
    _raises(ValueError, PL, m.stage_peaks, [(S('a'), 'b', 1)])
    _raises(ValueError, HO, m.stage_peaks, [('a', S('b'), 1)])
    _raises(ValueError, SE, m.stage_peaks, [('a', 'b', I(1))])
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
    ('type(play) is not str', 'not isinstance(play, str)'),
    ('type(house) is not str', 'not isinstance(house, str)'),
    ('type(seats) is not int', 'not isinstance(seats, int)'),
    ('not 1 <= len(play) <= 16', 'not 1 <= len(play) <= 17'),
    ('not 1 <= len(house) <= 16', 'not 1 <= len(house) <= 17'),
    ('not 1 <= seats <= 9', 'not 1 <= seats <= 10'),
    ('        elif seats > peaks[house]:', '        elif seats < peaks[house]:'),
    ('        elif seats > peaks[house]:', '        elif seats >= peaks[house]:'),
    ('            peak_rows[house] = pos', '            peak_rows[house] = 0'),
    ('        last_rows[house] = pos', '        last_rows[house] = 1'),
    ('if earliest is None or peak_rows[house] < peak_rows[earliest]:',
     'if earliest is None or peak_rows[house] > peak_rows[earliest]:'),
    ('if peak_rows[h] == last_rows[h]', 'if peak_rows[h] != last_rows[h]'),
    ("'peak_rows': peak_rows", "'peak_rows': last_rows"),
    ("'earliest': earliest", "'earliest': None"),
    ("'closers': closers", "'closers': []"),
    ("'total': len(rows)", "'total': len(peak_rows)"),
    ('        play, house, seats = row', '        house, play, seats = row'),
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
    assert mod.stage_peaks([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.stage_peaks([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.stage_peaks([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
