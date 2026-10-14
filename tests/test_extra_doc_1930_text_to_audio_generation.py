import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import text_to_audio_generation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
TR = 'row 1: track must be a string of 1 to 16 characters'
GE = 'row 1: generator must be a string of 1 to 16 characters'
TO = 'row 1: tone must be a nonbool integer between 1 and 9'


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
    assert section == ('audio fidelity, timbre modeling, '
                       'sampling quality, licensing clearance, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: distinct-tone counting over supplied rows'
    assert mod.NOT_CLAIMED == ('audio fidelity', 'timbre modeling',
                               'sampling quality', 'licensing clearance',
                               'production readiness')


def _expected(rows):
    seen = {}
    supplied = {}
    for track, generator, tone in rows:
        if generator not in seen:
            seen[generator] = set()
            supplied[generator] = 0
        seen[generator].add(tone)
        supplied[generator] += 1
    distinct = {}
    for generator in seen:
        distinct[generator] = len(seen[generator])
    varied = sorted(g for g in distinct if distinct[g] == supplied[g])
    richest = None
    for generator in distinct:
        if richest is None or distinct[generator] > distinct[richest]:
            richest = generator
    return {'total': len(rows), 'distinct': distinct,
            'varied': varied, 'richest': richest}


def _core(m):
    # fixed pins, oracle seeded with row number 1930
    assert m.distinct_tones([('t', 'g1', 1), ('t', 'g1', 2), ('t', 'g1', 3),
                             ('t', 'g2', 5), ('t', 'g2', 5)]) == {
        'total': 5, 'distinct': {'g1': 3, 'g2': 1},
        'varied': ['g1'], 'richest': 'g1'}
    # one row is always varied
    assert m.distinct_tones([('t', 'g', 4)]) == {
        'total': 1, 'distinct': {'g': 1}, 'varied': ['g'], 'richest': 'g'}
    # a repeat breaks variety
    assert m.distinct_tones([('t', 'x', 2), ('t', 'x', 2)]) == {
        'total': 2, 'distinct': {'x': 1}, 'varied': [], 'richest': 'x'}
    # the richest tie goes to the first supplied generator
    r = m.distinct_tones([('t', 'Üser-9!', 1), ('t', 'q?7', 2)])
    assert r == {'total': 2, 'distinct': {'Üser-9!': 1, 'q?7': 1},
                 'varied': ['q?7', 'Üser-9!'], 'richest': 'Üser-9!'}
    # dicts keep first-touch order
    r = m.distinct_tones([('z', 'b', 7), ('a', 'a', 2)])
    assert r['distinct'] == {'b': 1, 'a': 1}
    # more distinct tones wins over an earlier generator
    r = m.distinct_tones([('t', 'p', 1), ('t', 'q', 1), ('t', 'q', 2)])
    assert r['distinct'] == {'p': 1, 'q': 2}
    assert r['varied'] == ['p', 'q'] and r['richest'] == 'q'
    # repeats can still hold the richest spot without being varied
    r = m.distinct_tones([('t', 'p', 1), ('t', 'p', 1), ('t', 'p', 2),
                          ('t', 'q', 5)])
    assert r == {'total': 4, 'distinct': {'p': 2, 'q': 1},
                 'varied': ['q'], 'richest': 'p'}
    # pre-seed pin: fresh accumulators only
    assert m.distinct_tones([('t', 'a', 1), ('t', 'a', 2), ('t', 'b', 9)]) == {
        'total': 3, 'distinct': {'a': 2, 'b': 1},
        'varied': ['a', 'b'], 'richest': 'a'}
    rng = random.Random(1930)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.distinct_tones(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.distinct_tones, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.distinct_tones, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.distinct_tones, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.distinct_tones, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (track, generator, tone) triple',
            m.distinct_tones, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.distinct_tones, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.distinct_tones, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, TR, m.distinct_tones, [(1, 'b', 1)])
    _raises(ValueError, TR, m.distinct_tones, [('', 'b', 1)])
    _raises(ValueError, TR, m.distinct_tones, [('x' * 17, 'b', 1)])
    _raises(ValueError, GE, m.distinct_tones, [('a', 1, 1)])
    _raises(ValueError, GE, m.distinct_tones, [('a', '', 1)])
    _raises(ValueError, GE, m.distinct_tones, [('a', 'x' * 17, 1)])
    _raises(ValueError, TO, m.distinct_tones, [('a', 'b', '1')])
    _raises(ValueError, TO, m.distinct_tones, [('a', 'b', 0)])
    _raises(ValueError, TO, m.distinct_tones, [('a', 'b', 10)])
    _raises(ValueError, TO, m.distinct_tones, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: track must be a string of 1 to 16 characters',
            m.distinct_tones, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: tone must be a nonbool integer between 1 and 9',
            m.distinct_tones, [('a', 'b', 1), ('c', 'd', 0)])
    # track is validated before generator, generator before tone
    _raises(ValueError, TR, m.distinct_tones, [('x' * 17, '', 0)])
    _raises(ValueError, GE, m.distinct_tones, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.distinct_tones, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.distinct_tones((('a', 'b', 1),)) == m.distinct_tones([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.distinct_tones([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.distinct_tones([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.distinct_tones([('a', 'b', 1)] * 60)['total'] == 60
    assert m.distinct_tones([('a', 'b', 9)])['distinct'] == {'b': 1}
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
        _raises(TypeError, P, m.distinct_tones, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (track, generator, tone) triple',
                m.distinct_tones, [K(('a', 'b', 1))])
    _raises(ValueError, TR, m.distinct_tones, [(S('a'), 'b', 1)])
    _raises(ValueError, GE, m.distinct_tones, [('a', S('b'), 1)])
    _raises(ValueError, TO, m.distinct_tones, [('a', 'b', I(1))])
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
    ('type(track) is not str', 'not isinstance(track, str)'),
    ('type(generator) is not str', 'not isinstance(generator, str)'),
    ('type(tone) is not int', 'not isinstance(tone, int)'),
    ('not 1 <= len(track) <= 16', 'not 1 <= len(track) <= 17'),
    ('not 1 <= len(generator) <= 16', 'not 1 <= len(generator) <= 17'),
    ('not 1 <= tone <= 9', 'not 1 <= tone <= 10'),
    ('            supplied[generator] = 0', '            supplied[generator] = 1'),
    ('        seen[generator].add(tone)', '        seen[generator].add(1)'),
    ('        supplied[generator] += 1', '        supplied[generator] += 2'),
    ('distinct[generator] = len(seen[generator])',
     'distinct[generator] = len(seen[generator]) + 1'),
    ('distinct[g] == supplied[g]', 'distinct[g] != supplied[g]'),
    ('if richest is None or distinct[generator] > distinct[richest]:',
     'if richest is None or distinct[generator] < distinct[richest]:'),
    ("'distinct': distinct", "'distinct': {}"),
    ("'varied': varied", "'varied': []"),
    ("'richest': richest", "'richest': None"),
    ("'total': len(rows)", "'total': len(distinct)"),
    ('        track, generator, tone = row',
     '        generator, track, tone = row'),
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
    assert mod.distinct_tones([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.distinct_tones([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.distinct_tones([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
