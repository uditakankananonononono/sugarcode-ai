import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ai_art as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PI = 'row 1: piece must be a string of 1 to 16 characters'
STU = 'row 1: studio must be a string of 1 to 16 characters'
WE = 'row 1: weight must be a nonbool integer between 1 and 9'


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
    assert section == ('aesthetic judgment, style originality, '
                       'training-data provenance, gallery placement, '
                       'commercial licensing.')
    assert mod.SCOPE == 'PARTIAL: alternating-pull sums over supplied rows'
    assert mod.NOT_CLAIMED == ('aesthetic judgment', 'style originality',
                               'training-data provenance', 'gallery placement',
                               'commercial licensing')


def _expected(rows):
    pulls = {}
    counts = {}
    for piece, studio, weight in rows:
        if studio not in pulls:
            pulls[studio] = 0
            counts[studio] = 0
        if counts[studio] % 2 == 0:
            pulls[studio] += weight
        else:
            pulls[studio] -= weight
        counts[studio] += 1
    rising = sorted(s for s in pulls if pulls[s] > 0)
    strongest = None
    for studio in pulls:
        if strongest is None or pulls[studio] > pulls[strongest]:
            strongest = studio
    return {'total': len(rows), 'pulls': pulls,
            'rising': rising, 'strongest': strongest}


def _core(m):
    # fixed pins, oracle seeded with row number 1934
    assert m.alternating_pull([('p', 's1', 9), ('p', 's1', 1), ('p', 's1', 9),
                               ('p', 's2', 2), ('p', 's2', 8)]) == {
        'total': 5, 'pulls': {'s1': 17, 's2': -6},
        'rising': ['s1'], 'strongest': 's1'}
    # a single row always rises
    assert m.alternating_pull([('p', 's', 5)]) == {
        'total': 1, 'pulls': {'s': 5}, 'rising': ['s'], 'strongest': 's'}
    # equal pairs cancel to zero, which does not rise
    assert m.alternating_pull([('p', 'x', 5), ('p', 'x', 5)]) == {
        'total': 2, 'pulls': {'x': 0}, 'rising': [], 'strongest': 'x'}
    # a heavy second weight sinks the pull
    assert m.alternating_pull([('p', 'x', 1), ('p', 'x', 9)]) == {
        'total': 2, 'pulls': {'x': -8}, 'rising': [], 'strongest': 'x'}
    # the strongest tie goes to the first supplied studio
    r = m.alternating_pull([('p', 'Üser-9!', 9), ('p', 'q?7', 9)])
    assert r == {'total': 2, 'pulls': {'Üser-9!': 9, 'q?7': 9},
                 'rising': ['q?7', 'Üser-9!'], 'strongest': 'Üser-9!'}
    # dicts keep first-touch order
    r = m.alternating_pull([('z', 'b', 7), ('a', 'a', 2)])
    assert r['pulls'] == {'b': 7, 'a': 2} and r['strongest'] == 'b'
    # the third weight adds again
    r = m.alternating_pull([('p', 'p', 1), ('p', 'q', 1),
                            ('p', 'q', 2), ('p', 'q', 9)])
    assert r['pulls'] == {'p': 1, 'q': 8}
    assert r['rising'] == ['p', 'q'] and r['strongest'] == 'q'
    # a late heavy negative can sink an early lead
    assert m.alternating_pull([('p', 'x', 9), ('p', 'x', 1),
                               ('p', 'x', 1), ('p', 'x', 9)]) == {
        'total': 4, 'pulls': {'x': 0}, 'rising': [], 'strongest': 'x'}
    # pre-seed pin: fresh accumulators only
    assert m.alternating_pull([('p', 'a', 9), ('p', 'a', 1),
                               ('p', 'b', 2), ('p', 'b', 2)]) == {
        'total': 4, 'pulls': {'a': 8, 'b': 0},
        'rising': ['a'], 'strongest': 'a'}
    rng = random.Random(1934)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.alternating_pull(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.alternating_pull, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.alternating_pull, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.alternating_pull, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.alternating_pull, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (piece, studio, weight) triple',
            m.alternating_pull, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.alternating_pull, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.alternating_pull, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PI, m.alternating_pull, [(1, 'b', 1)])
    _raises(ValueError, PI, m.alternating_pull, [('', 'b', 1)])
    _raises(ValueError, PI, m.alternating_pull, [('x' * 17, 'b', 1)])
    _raises(ValueError, STU, m.alternating_pull, [('a', 1, 1)])
    _raises(ValueError, STU, m.alternating_pull, [('a', '', 1)])
    _raises(ValueError, STU, m.alternating_pull, [('a', 'x' * 17, 1)])
    _raises(ValueError, WE, m.alternating_pull, [('a', 'b', '1')])
    _raises(ValueError, WE, m.alternating_pull, [('a', 'b', 0)])
    _raises(ValueError, WE, m.alternating_pull, [('a', 'b', 10)])
    _raises(ValueError, WE, m.alternating_pull, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: piece must be a string of 1 to 16 characters',
            m.alternating_pull, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: weight must be a nonbool integer between 1 and 9',
            m.alternating_pull, [('a', 'b', 1), ('c', 'd', 0)])
    # piece is validated before studio, studio before weight
    _raises(ValueError, PI, m.alternating_pull, [('x' * 17, '', 0)])
    _raises(ValueError, STU, m.alternating_pull, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.alternating_pull, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.alternating_pull((('a', 'b', 1),)) == m.alternating_pull([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.alternating_pull([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.alternating_pull([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.alternating_pull([('a', 'b', 1)] * 60)['total'] == 60
    assert m.alternating_pull([('a', 'b', 9)])['pulls'] == {'b': 9}
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
        _raises(TypeError, P, m.alternating_pull, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (piece, studio, weight) triple',
                m.alternating_pull, [K(('a', 'b', 1))])
    _raises(ValueError, PI, m.alternating_pull, [(S('a'), 'b', 1)])
    _raises(ValueError, STU, m.alternating_pull, [('a', S('b'), 1)])
    _raises(ValueError, WE, m.alternating_pull, [('a', 'b', I(1))])
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
    ('type(piece) is not str', 'not isinstance(piece, str)'),
    ('type(studio) is not str', 'not isinstance(studio, str)'),
    ('type(weight) is not int', 'not isinstance(weight, int)'),
    ('not 1 <= len(piece) <= 16', 'not 1 <= len(piece) <= 17'),
    ('not 1 <= len(studio) <= 16', 'not 1 <= len(studio) <= 17'),
    ('not 1 <= weight <= 9', 'not 1 <= weight <= 10'),
    ('            pulls[studio] = 0', '            pulls[studio] = 1'),
    ('            counts[studio] = 0', '            counts[studio] = 1'),
    ('        if counts[studio] % 2 == 0:', '        if counts[studio] % 2 == 1:'),
    ('            pulls[studio] += weight', '            pulls[studio] -= weight'),
    ('            pulls[studio] -= weight', '            pulls[studio] += weight'),
    ('pulls[s] > 0', 'pulls[s] >= 0'),
    ('if strongest is None or pulls[studio] > pulls[strongest]:',
     'if strongest is None or pulls[studio] < pulls[strongest]:'),
    ("'pulls': pulls", "'pulls': {}"),
    ("'rising': rising", "'rising': []"),
    ("'strongest': strongest", "'strongest': None"),
    ("'total': len(rows)", "'total': len(pulls)"),
    ('        piece, studio, weight = row',
     '        studio, piece, weight = row'),
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
    assert mod.alternating_pull([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.alternating_pull([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.alternating_pull([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
