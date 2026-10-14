import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import folklore as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TL = 'row 1: tale must be a string of 1 to 16 characters'
MT = 'row 1: motif must be a string of 1 to 16 characters'
CH = 'row 1: charm must be a nonbool integer between 1 and 9'


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
    assert section == ('oral tradition, tale typing, fieldwork, '
                       'performance studies, production readiness.')
    assert mod.SCOPE == 'PARTIAL: motif tracing over supplied charms'
    assert mod.NOT_CLAIMED == ('oral tradition', 'tale typing', 'fieldwork',
                               'performance studies',
                               'production readiness')


def _expected(rows):
    echoes = 0
    marked = {}
    for j in range(len(rows) - 1):
        if rows[j][1] == rows[j + 1][1]:
            echoes += 1
            marked[rows[j][1]] = True
    echoing = sorted(marked)
    totals = {}
    for tale, motif, charm in rows:
        if tale not in totals:
            totals[tale] = 0
        totals[tale] += charm
    richest = None
    for tale in totals:
        if richest is None or totals[tale] > totals[richest]:
            richest = tale
    return {'total': len(rows), 'echoes': echoes, 'echoing': echoing,
            'totals': totals, 'richest': richest}


def _core(m):
    # fixed pins, oracle seeded with row number 1905
    assert m.trace_motifs([('t1', 'a', 3), ('t1', 'a', 5), ('t2', 'b', 2),
                           ('t2', 'b', 4), ('t2', 'b', 1)]) == {
        'total': 5, 'echoes': 3, 'echoing': ['a', 'b'],
        'totals': {'t1': 8, 't2': 7}, 'richest': 't1'}
    # one row has no adjacent pair
    assert m.trace_motifs([('t', 'm', 5)]) == {
        'total': 1, 'echoes': 0, 'echoing': [],
        'totals': {'t': 5}, 'richest': 't'}
    # alternating motifs echo nothing
    r = m.trace_motifs([('t', 'a', 1), ('t', 'b', 1), ('t', 'a', 1)])
    assert r['echoes'] == 0 and r['echoing'] == []
    # an echo can span two tales
    r = m.trace_motifs([('t1', 'a', 1), ('t2', 'a', 1)])
    assert r['echoes'] == 1 and r['echoing'] == ['a']
    # a run of three equal motifs is two echoes
    r = m.trace_motifs([('t', 'a', 1), ('t', 'a', 2), ('t', 'a', 3)])
    assert r['echoes'] == 2 and r['echoing'] == ['a']
    # the richest tie goes to the first supplied tale
    assert m.trace_motifs([('x', 'm', 9), ('y', 'n', 9)])['richest'] == 'x'
    # dicts keep first-touch order
    r = m.trace_motifs([('z', 'm', 1), ('a', 'n', 2)])
    assert r['totals'] == {'z': 1, 'a': 2}
    # non-ASCII tales and motifs follow the same rule
    r = m.trace_motifs([('Üser-9!', 'Ω-1', 9), ('Üser-9!', 'Ω-1', 8),
                        ('q?7', 'a', 1)])
    assert r == {'total': 3, 'echoes': 1, 'echoing': ['Ω-1'],
                 'totals': {'Üser-9!': 17, 'q?7': 1},
                 'richest': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.trace_motifs([('p', 'a', 4), ('p', 'a', 4), ('q', 'b', 9)]) == {
        'total': 3, 'echoes': 1, 'echoing': ['a'],
        'totals': {'p': 8, 'q': 9}, 'richest': 'q'}
    rng = random.Random(1905)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.trace_motifs(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.trace_motifs, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.trace_motifs, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.trace_motifs, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.trace_motifs, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (tale, motif, charm) triple',
            m.trace_motifs, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.trace_motifs, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.trace_motifs, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TL, m.trace_motifs, [(1, 'b', 1)])
    _raises(ValueError, TL, m.trace_motifs, [('', 'b', 1)])
    _raises(ValueError, TL, m.trace_motifs, [('x' * 17, 'b', 1)])
    _raises(ValueError, MT, m.trace_motifs, [('a', 1, 1)])
    _raises(ValueError, MT, m.trace_motifs, [('a', '', 1)])
    _raises(ValueError, MT, m.trace_motifs, [('a', 'x' * 17, 1)])
    _raises(ValueError, CH, m.trace_motifs, [('a', 'b', '1')])
    _raises(ValueError, CH, m.trace_motifs, [('a', 'b', 0)])
    _raises(ValueError, CH, m.trace_motifs, [('a', 'b', 10)])
    _raises(ValueError, CH, m.trace_motifs, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: tale must be a string of 1 to 16 characters',
            m.trace_motifs, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: charm must be a nonbool integer between 1 and 9',
            m.trace_motifs, [('a', 'b', 1), ('c', 'd', 0)])
    # tale is validated before motif, motif before charm
    _raises(ValueError, TL, m.trace_motifs, [('x' * 17, '', 0)])
    _raises(ValueError, MT, m.trace_motifs, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.trace_motifs, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.trace_motifs((('a', 'b', 1),)) == m.trace_motifs([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.trace_motifs([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.trace_motifs([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.trace_motifs([('a', 'b', 1)] * 60)['total'] == 60
    assert m.trace_motifs([('a', 'b', 9)])['echoes'] == 0
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
        _raises(TypeError, P, m.trace_motifs, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (tale, motif, charm) triple',
                m.trace_motifs, [K(('a', 'b', 1))])
    _raises(ValueError, TL, m.trace_motifs, [(S('a'), 'b', 1)])
    _raises(ValueError, MT, m.trace_motifs, [('a', S('b'), 1)])
    _raises(ValueError, CH, m.trace_motifs, [('a', 'b', I(1))])
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
    ('type(tale) is not str', 'not isinstance(tale, str)'),
    ('type(motif) is not str', 'not isinstance(motif, str)'),
    ('type(charm) is not int', 'not isinstance(charm, int)'),
    ('not 1 <= len(tale) <= 16', 'not 1 <= len(tale) <= 17'),
    ('not 1 <= len(motif) <= 16', 'not 1 <= len(motif) <= 17'),
    ('not 1 <= charm <= 9', 'not 1 <= charm <= 10'),
    ('    for j in range(len(rows) - 1):', '    for j in range(len(rows)):'),
    ('        if rows[j][1] == rows[j + 1][1]:',
     '        if rows[j][1] != rows[j + 1][1]:'),
    ('            echoes += 1', '            echoes += 2'),
    ('        totals[tale] += charm', '        totals[tale] += 1'),
    ('if richest is None or totals[tale] > totals[richest]:',
     'if richest is None or totals[tale] < totals[richest]:'),
    ("'echoes': echoes", "'echoes': len(echoing)"),
    ("'totals': totals", "'totals': marked"),
    ("'echoing': echoing", "'echoing': []"),
    ("'total': len(rows)", "'total': len(totals)"),
    ('        tale, motif, charm = row',
     '        motif, tale, charm = row'),
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
    assert mod.trace_motifs([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.trace_motifs([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.trace_motifs([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
