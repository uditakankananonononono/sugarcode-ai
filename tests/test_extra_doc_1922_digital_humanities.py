import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import digital_humanities as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
CO = 'row 1: corpus must be a string of 1 to 16 characters'
TO = 'row 1: tool must be a string of 1 to 16 characters'
GN = 'row 1: gain must be a nonbool integer between 1 and 9'


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
    assert section == ('corpus linguistics, digitization ethics, '
                       'archival policy, tool benchmarking, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: flawless marking over supplied gains'
    assert mod.NOT_CLAIMED == ('corpus linguistics', 'digitization ethics',
                               'archival policy', 'tool benchmarking',
                               'production readiness')


def _expected(rows):
    counts = {}
    nines = {}
    for corpus, tool, gain in rows:
        if corpus not in counts:
            counts[corpus] = 0
            nines[corpus] = 0
        counts[corpus] += 1
        if gain == 9:
            nines[corpus] += 1
    polished = sorted(c for c in counts
                      if counts[c] >= 2 and nines[c] == counts[c])
    most_nines = None
    for corpus in nines:
        if most_nines is None or nines[corpus] > nines[most_nines]:
            most_nines = corpus
    return {'total': len(rows), 'nines': nines,
            'polished': polished, 'most_nines': most_nines}


def _core(m):
    # fixed pins, oracle seeded with row number 1922
    assert m.mark_flawless([('c1', 't', 9), ('c1', 't', 9), ('c2', 't', 9),
                            ('c2', 't', 8), ('c3', 't', 9)]) == {
        'total': 5, 'nines': {'c1': 2, 'c2': 1, 'c3': 1},
        'polished': ['c1'], 'most_nines': 'c1'}
    # no nines at all
    assert m.mark_flawless([('c', 't', 5)]) == {
        'total': 1, 'nines': {'c': 0}, 'polished': [], 'most_nines': 'c'}
    # a lone 9 is not yet polished
    assert m.mark_flawless([('a', 'x', 9), ('b', 'y', 9)]) == {
        'total': 2, 'nines': {'a': 1, 'b': 1},
        'polished': [], 'most_nines': 'a'}
    # eights never count
    assert m.mark_flawless([('a', 'x', 8), ('a', 'y', 8)])['nines'] == {'a': 0}
    # the most-nines tie goes to the first supplied corpus
    r = m.mark_flawless([('a', 'x', 9), ('a', 'x', 9),
                         ('b', 'y', 9), ('b', 'y', 9)])
    assert r['nines'] == {'a': 2, 'b': 2} and r['most_nines'] == 'a'
    assert r['polished'] == ['a', 'b']
    # dicts keep first-touch order
    r = m.mark_flawless([('z', 'b', 9), ('a', 'a', 1)])
    assert r['nines'] == {'z': 1, 'a': 0}
    # non-ASCII corpora follow the same rule
    r = m.mark_flawless([('Üser-9!', 't', 9), ('q?7', 't', 9),
                         ('Üser-9!', 't', 9), ('q?7', 't', 9)])
    assert r == {'total': 4, 'nines': {'Üser-9!': 2, 'q?7': 2},
                 'polished': ['q?7', 'Üser-9!'], 'most_nines': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.mark_flawless([('p', 't', 9), ('p', 't', 8),
                            ('q', 't', 9), ('q', 't', 9)]) == {
        'total': 4, 'nines': {'p': 1, 'q': 2},
        'polished': ['q'], 'most_nines': 'q'}
    rng = random.Random(1922)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.mark_flawless(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.mark_flawless, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.mark_flawless, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.mark_flawless, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.mark_flawless, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (corpus, tool, gain) triple',
            m.mark_flawless, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.mark_flawless, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.mark_flawless, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, CO, m.mark_flawless, [(1, 'b', 1)])
    _raises(ValueError, CO, m.mark_flawless, [('', 'b', 1)])
    _raises(ValueError, CO, m.mark_flawless, [('x' * 17, 'b', 1)])
    _raises(ValueError, TO, m.mark_flawless, [('a', 1, 1)])
    _raises(ValueError, TO, m.mark_flawless, [('a', '', 1)])
    _raises(ValueError, TO, m.mark_flawless, [('a', 'x' * 17, 1)])
    _raises(ValueError, GN, m.mark_flawless, [('a', 'b', '1')])
    _raises(ValueError, GN, m.mark_flawless, [('a', 'b', 0)])
    _raises(ValueError, GN, m.mark_flawless, [('a', 'b', 10)])
    _raises(ValueError, GN, m.mark_flawless, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: corpus must be a string of 1 to 16 characters',
            m.mark_flawless, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: gain must be a nonbool integer between 1 and 9',
            m.mark_flawless, [('a', 'b', 1), ('c', 'd', 0)])
    # corpus is validated before tool, tool before gain
    _raises(ValueError, CO, m.mark_flawless, [('x' * 17, '', 0)])
    _raises(ValueError, TO, m.mark_flawless, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.mark_flawless, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.mark_flawless((('a', 'b', 1),)) == m.mark_flawless([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.mark_flawless([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.mark_flawless([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.mark_flawless([('a', 'b', 1)] * 60)['total'] == 60
    assert m.mark_flawless([('a', 'b', 9)])['nines'] == {'a': 1}
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
        _raises(TypeError, P, m.mark_flawless, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (corpus, tool, gain) triple',
                m.mark_flawless, [K(('a', 'b', 1))])
    _raises(ValueError, CO, m.mark_flawless, [(S('a'), 'b', 1)])
    _raises(ValueError, TO, m.mark_flawless, [('a', S('b'), 1)])
    _raises(ValueError, GN, m.mark_flawless, [('a', 'b', I(1))])
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
    ('type(corpus) is not str', 'not isinstance(corpus, str)'),
    ('type(tool) is not str', 'not isinstance(tool, str)'),
    ('type(gain) is not int', 'not isinstance(gain, int)'),
    ('not 1 <= len(corpus) <= 16', 'not 1 <= len(corpus) <= 17'),
    ('not 1 <= len(tool) <= 16', 'not 1 <= len(tool) <= 17'),
    ('not 1 <= gain <= 9', 'not 1 <= gain <= 10'),
    ('        counts[corpus] += 1', '        counts[corpus] += 2'),
    ('        if gain == 9:', '        if gain == 8:'),
    ('            nines[corpus] += 1', '            nines[corpus] += 2'),
    ('if counts[c] >= 2 and nines[c] == counts[c]',
     'if counts[c] >= 1 and nines[c] == counts[c]'),
    ('if most_nines is None or nines[corpus] > nines[most_nines]:',
     'if most_nines is None or nines[corpus] < nines[most_nines]:'),
    ("'nines': nines", "'nines': counts"),
    ("'polished': polished", "'polished': []"),
    ("'most_nines': most_nines", "'most_nines': None"),
    ("'total': len(rows)", "'total': len(nines)"),
    ('        corpus, tool, gain = row', '        tool, corpus, gain = row'),
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
    assert mod.mark_flawless([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.mark_flawless([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.mark_flawless([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
