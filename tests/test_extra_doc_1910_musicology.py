import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import musicology as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PC = 'row 1: piece must be a string of 1 to 16 characters'
CM = 'row 1: composer must be a string of 1 to 16 characters'
TM = 'row 1: tempo must be a nonbool integer between 1 and 9'


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
    assert section == ('music theory, performance practice, notation, '
                       'acoustics, production readiness.')
    assert mod.SCOPE == 'PARTIAL: piece tracing over supplied tempos'
    assert mod.NOT_CLAIMED == ('music theory', 'performance practice',
                               'notation', 'acoustics',
                               'production readiness')


def _expected(rows):
    seqs = {}
    for piece, composer, tempo in rows:
        if piece not in seqs:
            seqs[piece] = []
        seqs[piece].append(tempo)
    turns = {}
    counts = {}
    for piece in seqs:
        counts[piece] = len(seqs[piece])
        total_turns = 0
        last_dir = 0
        prev = None
        for tempo in seqs[piece]:
            if prev is not None and tempo != prev:
                d = 1 if tempo > prev else -1
                if last_dir != 0 and d != last_dir:
                    total_turns += 1
                last_dir = d
            prev = tempo
        turns[piece] = total_turns
    steady = sorted(p for p in turns if counts[p] >= 2 and turns[p] == 0)
    restless = sorted(p for p in turns if turns[p] >= 2)
    wildest = None
    for piece in turns:
        if wildest is None or turns[piece] > turns[wildest]:
            wildest = piece
    return {'total': len(rows), 'turns': turns, 'steady': steady,
            'restless': restless, 'wildest': wildest}


def _core(m):
    # fixed pins, oracle seeded with row number 1910
    assert m.trace_pieces([('p1', 'a', 1), ('p1', 'b', 5), ('p1', 'c', 2),
                           ('p1', 'd', 9), ('p2', 'e', 3), ('p2', 'f', 3)]) == {
        'total': 6, 'turns': {'p1': 2, 'p2': 0}, 'steady': ['p2'],
        'restless': ['p1'], 'wildest': 'p1'}
    # one row: no direction yet, and never steady
    assert m.trace_pieces([('p', 'c', 5)]) == {
        'total': 1, 'turns': {'p': 0}, 'steady': [],
        'restless': [], 'wildest': 'p'}
    # a monotone run has no turns and is steady
    r = m.trace_pieces([('p', 'a', 1), ('p', 'b', 2), ('p', 'c', 3)])
    assert r['turns'] == {'p': 0} and r['steady'] == ['p']
    # equal steps do not set or change direction
    r = m.trace_pieces([('p', 'a', 1), ('p', 'b', 1), ('p', 'c', 2),
                        ('p', 'd', 2), ('p', 'e', 1)])
    assert r['turns'] == {'p': 1}
    # one turn is not yet restless
    r = m.trace_pieces([('p', 'a', 1), ('p', 'b', 9), ('p', 'c', 1)])
    assert r['turns'] == {'p': 1} and r['restless'] == []
    # the wildest tie goes to the first supplied piece
    r = m.trace_pieces([('a', 'c', 1), ('a', 'c', 9), ('a', 'c', 1),
                        ('b', 'c', 1), ('b', 'c', 9), ('b', 'c', 1)])
    assert r['turns'] == {'a': 1, 'b': 1} and r['wildest'] == 'a'
    # dicts keep first-touch order
    r = m.trace_pieces([('z', 'c', 1), ('a', 'c', 2)])
    assert r['turns'] == {'z': 0, 'a': 0}
    # non-ASCII pieces follow the same rule
    r = m.trace_pieces([('Üser-9!', 'a', 1), ('Üser-9!', 'b', 9),
                        ('Üser-9!', 'c', 1), ('q?7', 'd', 4), ('q?7', 'e', 4)])
    assert r == {'total': 5, 'turns': {'Üser-9!': 1, 'q?7': 0},
                 'steady': ['q?7'], 'restless': [], 'wildest': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.trace_pieces([('p', 'a', 1), ('p', 'b', 9), ('p', 'c', 9),
                           ('p', 'd', 1), ('q', 'e', 5)]) == {
        'total': 5, 'turns': {'p': 1, 'q': 0}, 'steady': [],
        'restless': [], 'wildest': 'p'}
    rng = random.Random(1910)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.trace_pieces(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.trace_pieces, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.trace_pieces, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.trace_pieces, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.trace_pieces, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (piece, composer, tempo) triple',
            m.trace_pieces, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.trace_pieces, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.trace_pieces, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PC, m.trace_pieces, [(1, 'b', 1)])
    _raises(ValueError, PC, m.trace_pieces, [('', 'b', 1)])
    _raises(ValueError, PC, m.trace_pieces, [('x' * 17, 'b', 1)])
    _raises(ValueError, CM, m.trace_pieces, [('a', 1, 1)])
    _raises(ValueError, CM, m.trace_pieces, [('a', '', 1)])
    _raises(ValueError, CM, m.trace_pieces, [('a', 'x' * 17, 1)])
    _raises(ValueError, TM, m.trace_pieces, [('a', 'b', '1')])
    _raises(ValueError, TM, m.trace_pieces, [('a', 'b', 0)])
    _raises(ValueError, TM, m.trace_pieces, [('a', 'b', 10)])
    _raises(ValueError, TM, m.trace_pieces, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: piece must be a string of 1 to 16 characters',
            m.trace_pieces, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: tempo must be a nonbool integer between 1 and 9',
            m.trace_pieces, [('a', 'b', 1), ('c', 'd', 0)])
    # piece is validated before composer, composer before tempo
    _raises(ValueError, PC, m.trace_pieces, [('x' * 17, '', 0)])
    _raises(ValueError, CM, m.trace_pieces, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.trace_pieces, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.trace_pieces((('a', 'b', 1),)) == m.trace_pieces([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.trace_pieces([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.trace_pieces([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.trace_pieces([('a', 'b', 1)] * 60)['total'] == 60
    assert m.trace_pieces([('a', 'b', 9)])['turns'] == {'a': 0}
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
        _raises(TypeError, P, m.trace_pieces, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (piece, composer, tempo) triple',
                m.trace_pieces, [K(('a', 'b', 1))])
    _raises(ValueError, PC, m.trace_pieces, [(S('a'), 'b', 1)])
    _raises(ValueError, CM, m.trace_pieces, [('a', S('b'), 1)])
    _raises(ValueError, TM, m.trace_pieces, [('a', 'b', I(1))])
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
    ('type(composer) is not str', 'not isinstance(composer, str)'),
    ('type(tempo) is not int', 'not isinstance(tempo, int)'),
    ('not 1 <= len(piece) <= 16', 'not 1 <= len(piece) <= 17'),
    ('not 1 <= len(composer) <= 16', 'not 1 <= len(composer) <= 17'),
    ('not 1 <= tempo <= 9', 'not 1 <= tempo <= 10'),
    ('            if prev is not None and tempo != prev:',
     '            if prev is not None and tempo == prev:'),
    ('        last_dir = 0', '        last_dir = 1'),
    ('        prev = tempo', '        prev = None'),
    ('                    total_turns += 1', '                    total_turns += 2'),
    ('if counts[p] >= 2 and turns[p] == 0',
     'if counts[p] >= 2 and turns[p] == 1'),
    ('if turns[p] >= 2', 'if turns[p] >= 3'),
    ('if wildest is None or turns[piece] > turns[wildest]:',
     'if wildest is None or turns[piece] < turns[wildest]:'),
    ("'steady': steady", "'steady': restless"),
    ("'turns': turns", "'turns': counts"),
    ("'total': len(rows)", "'total': len(turns)"),
    ('        piece, composer, tempo = row',
     '        composer, piece, tempo = row'),
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
    assert mod.trace_pieces([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.trace_pieces([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.trace_pieces([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
