import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import multimodal_ai as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
ST = 'row 1: stream must be a string of 1 to 16 characters'
EN = 'row 1: encoder must be a string of 1 to 16 characters'
DE = 'row 1: depth must be a nonbool integer between 1 and 9'


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
    assert section == ('encoder design, fusion strategy, training data, '
                       'latency, production readiness.')
    assert mod.SCOPE == 'PARTIAL: ladder climbing over supplied depths'
    assert mod.NOT_CLAIMED == ('encoder design', 'fusion strategy',
                               'training data', 'latency',
                               'production readiness')


def _expected(rows):
    depths = {}
    for stream, encoder, depth in rows:
        if stream not in depths:
            depths[stream] = {}
        depths[stream][depth] = True
    spans = {}
    ladders = []
    for stream in depths:
        low = min(depths[stream])
        high = max(depths[stream])
        spans[stream] = len(depths[stream])
        if high - low == spans[stream] - 1:
            ladders.append(stream)
    tallest = None
    for stream in ladders:
        if tallest is None or spans[stream] > spans[tallest]:
            tallest = stream
    return {'total': len(rows), 'spans': spans,
            'ladders': sorted(ladders), 'tallest': tallest}


def _core(m):
    # fixed pins, oracle seeded with row number 1925
    assert m.climb_ladders([('s1', 'e', 2), ('s1', 'e', 3), ('s1', 'e', 4),
                            ('s2', 'e', 1), ('s2', 'e', 9)]) == {
        'total': 5, 'spans': {'s1': 3, 's2': 2},
        'ladders': ['s1'], 'tallest': 's1'}
    # one depth is always a ladder of span 1
    assert m.climb_ladders([('s', 'e', 5)]) == {
        'total': 1, 'spans': {'s': 1}, 'ladders': ['s'], 'tallest': 's'}
    # repeats do not widen a span
    assert m.climb_ladders([('a', 'x', 3), ('a', 'y', 3)]) == {
        'total': 2, 'spans': {'a': 1}, 'ladders': ['a'], 'tallest': 'a'}
    # a gap of one depth breaks the ladder
    assert m.climb_ladders([('a', 'x', 2), ('a', 'y', 4)]) == {
        'total': 2, 'spans': {'a': 2}, 'ladders': [], 'tallest': None}
    # the tallest tie goes to the first supplied stream
    r = m.climb_ladders([('Üser-9!', 'e', 4), ('q?7', 'e', 2),
                         ('Üser-9!', 'e', 5), ('q?7', 'e', 3)])
    assert r == {'total': 4, 'spans': {'Üser-9!': 2, 'q?7': 2},
                 'ladders': ['q?7', 'Üser-9!'], 'tallest': 'Üser-9!'}
    # dicts keep first-touch order
    r = m.climb_ladders([('z', 'b', 7), ('a', 'a', 2)])
    assert r['spans'] == {'z': 1, 'a': 1}
    # a longer ladder beats an earlier shorter one
    r = m.climb_ladders([('q', 'e', 5), ('q', 'e', 6),
                         ('p', 'e', 1), ('p', 'e', 2), ('p', 'e', 3)])
    assert r['ladders'] == ['p', 'q'] and r['tallest'] == 'p'
    # pre-seed pin: fresh accumulators only
    assert m.climb_ladders([('p', 'e', 7), ('p', 'e', 8),
                            ('q', 'e', 1), ('q', 'e', 3)]) == {
        'total': 4, 'spans': {'p': 2, 'q': 2},
        'ladders': ['p'], 'tallest': 'p'}
    rng = random.Random(1925)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.climb_ladders(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.climb_ladders, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.climb_ladders, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.climb_ladders, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.climb_ladders, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (stream, encoder, depth) triple',
            m.climb_ladders, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.climb_ladders, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.climb_ladders, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, ST, m.climb_ladders, [(1, 'b', 1)])
    _raises(ValueError, ST, m.climb_ladders, [('', 'b', 1)])
    _raises(ValueError, ST, m.climb_ladders, [('x' * 17, 'b', 1)])
    _raises(ValueError, EN, m.climb_ladders, [('a', 1, 1)])
    _raises(ValueError, EN, m.climb_ladders, [('a', '', 1)])
    _raises(ValueError, EN, m.climb_ladders, [('a', 'x' * 17, 1)])
    _raises(ValueError, DE, m.climb_ladders, [('a', 'b', '1')])
    _raises(ValueError, DE, m.climb_ladders, [('a', 'b', 0)])
    _raises(ValueError, DE, m.climb_ladders, [('a', 'b', 10)])
    _raises(ValueError, DE, m.climb_ladders, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: stream must be a string of 1 to 16 characters',
            m.climb_ladders, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: depth must be a nonbool integer between 1 and 9',
            m.climb_ladders, [('a', 'b', 1), ('c', 'd', 0)])
    # stream is validated before encoder, encoder before depth
    _raises(ValueError, ST, m.climb_ladders, [('x' * 17, '', 0)])
    _raises(ValueError, EN, m.climb_ladders, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.climb_ladders, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.climb_ladders((('a', 'b', 1),)) == m.climb_ladders([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.climb_ladders([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.climb_ladders([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.climb_ladders([('a', 'b', 1)] * 60)['total'] == 60
    assert m.climb_ladders([('a', 'b', 9)])['spans'] == {'a': 1}
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
        _raises(TypeError, P, m.climb_ladders, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (stream, encoder, depth) triple',
                m.climb_ladders, [K(('a', 'b', 1))])
    _raises(ValueError, ST, m.climb_ladders, [(S('a'), 'b', 1)])
    _raises(ValueError, EN, m.climb_ladders, [('a', S('b'), 1)])
    _raises(ValueError, DE, m.climb_ladders, [('a', 'b', I(1))])
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
    ('type(stream) is not str', 'not isinstance(stream, str)'),
    ('type(encoder) is not str', 'not isinstance(encoder, str)'),
    ('type(depth) is not int', 'not isinstance(depth, int)'),
    ('not 1 <= len(stream) <= 16', 'not 1 <= len(stream) <= 17'),
    ('not 1 <= len(encoder) <= 16', 'not 1 <= len(encoder) <= 17'),
    ('not 1 <= depth <= 9', 'not 1 <= depth <= 10'),
    ('        depths[stream][depth] = True', '        depths[stream] = {}'),
    ('        low = min(depths[stream])', '        low = max(depths[stream])'),
    ('        spans[stream] = len(depths[stream])',
     '        spans[stream] = len(depths[stream]) + 1'),
    ('if high - low == spans[stream] - 1:',
     'if high - low == spans[stream]:'),
    ('if tallest is None or spans[stream] > spans[tallest]:',
     'if tallest is None or spans[stream] < spans[tallest]:'),
    ("'spans': spans", "'spans': {}"),
    ("'ladders': sorted(ladders)", "'ladders': []"),
    ("'tallest': tallest", "'tallest': None"),
    ("'total': len(rows)", "'total': len(spans)"),
    ('        stream, encoder, depth = row',
     '        encoder, stream, depth = row'),
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
    assert mod.climb_ladders([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.climb_ladders([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.climb_ladders([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
