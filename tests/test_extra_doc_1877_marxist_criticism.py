import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import marxist_criticism as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
WM = 'row 1: work must be a string of 1 to 16 characters'
FM = 'row 1: faction must be a string of 1 to 16 characters'
XM = 'row 1: wealth must be a nonbool integer between 1 and 9'


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
    assert section == ('historical materialism, class consciousness, '
                       'ideology critique, economic determinism, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: wealth-gap tallying over supplied factions'
    assert mod.NOT_CLAIMED == ('historical materialism', 'class consciousness',
                               'ideology critique', 'economic determinism',
                               'production readiness')


def _expected(rows):
    holdings = {}
    for work, faction, wealth in rows:
        if work not in holdings:
            holdings[work] = {}
        if faction not in holdings[work]:
            holdings[work][faction] = 0
        holdings[work][faction] += wealth
    gap = {}
    for work in holdings:
        richest = None
        for faction in holdings[work]:
            if richest is None or holdings[work][faction] > richest:
                richest = holdings[work][faction]
        poorest = None
        for faction in holdings[work]:
            if poorest is None or holdings[work][faction] < poorest:
                poorest = holdings[work][faction]
        gap[work] = richest - poorest
    polarized = sorted(work for work in gap if gap[work] >= 7)
    egalitarian = sorted(work for work in gap if gap[work] == 0)
    widest = None
    for work in gap:
        if widest is None or gap[work] > gap[widest]:
            widest = work
    return {'total': len(rows), 'gap': gap, 'polarized': polarized,
            'egalitarian': egalitarian, 'widest': widest}


def _core(m):
    # fixed pins, oracle seeded with row number 1877
    assert m.class_struggle([('novel', 'bourgeois', 9),
                             ('novel', 'proletariat', 2),
                             ('novel', 'proletariat', 1),
                             ('epic', 'a', 5), ('epic', 'b', 5)]) == {
        'total': 5, 'gap': {'novel': 6, 'epic': 0},
        'polarized': [], 'egalitarian': ['epic'], 'widest': 'novel'}
    # one row: a lone faction leaves no gap
    assert m.class_struggle([('w', 'f', 5)]) == {
        'total': 1, 'gap': {'w': 0}, 'polarized': [],
        'egalitarian': ['w'], 'widest': 'w'}
    # a gap of exactly 7 is polarized, 6 is not
    r = m.class_struggle([('w', 'a', 9), ('w', 'b', 1), ('w', 'b', 1)])
    assert r['gap'] == {'w': 7} and r['polarized'] == ['w']
    # the widest tie goes to the first supplied
    r = m.class_struggle([('x', 'a', 9), ('x', 'b', 1),
                          ('y', 'c', 9), ('y', 'd', 1)])
    assert r['gap'] == {'x': 8, 'y': 8} and r['widest'] == 'x'
    assert r['polarized'] == ['x', 'y'] and r['egalitarian'] == []
    # faction totals decide the gap, not single rows
    r = m.class_struggle([('w', 'a', 5), ('w', 'a', 5), ('w', 'b', 9)])
    assert r['gap'] == {'w': 1}
    assert r['polarized'] == [] and r['egalitarian'] == []
    # all-zero gaps: widest is the first supplied work
    r = m.class_struggle([('a', 'x', 1), ('b', 'y', 2)])
    assert r['gap'] == {'a': 0, 'b': 0} and r['widest'] == 'a'
    assert r['egalitarian'] == ['a', 'b']
    # dicts keep first-touch order
    r = m.class_struggle([('z', 'f', 1), ('a', 'g', 2)])
    assert r['gap'] == {'z': 0, 'a': 0}
    # non-ASCII works and factions follow the same rule
    r = m.class_struggle([('Üser-9!', 'Ω-1', 9), ('Üser-9!', 'q?7', 1)])
    assert r == {'total': 2, 'gap': {'Üser-9!': 8}, 'polarized': ['Üser-9!'],
                 'egalitarian': [], 'widest': 'Üser-9!'}
    rng = random.Random(1877)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.class_struggle(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.class_struggle, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.class_struggle, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.class_struggle, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.class_struggle, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (work, faction, wealth) triple',
            m.class_struggle, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.class_struggle, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.class_struggle, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, WM, m.class_struggle, [(1, 'b', 1)])
    _raises(ValueError, WM, m.class_struggle, [('', 'b', 1)])
    _raises(ValueError, WM, m.class_struggle, [('x' * 17, 'b', 1)])
    _raises(ValueError, FM, m.class_struggle, [('a', 1, 1)])
    _raises(ValueError, FM, m.class_struggle, [('a', '', 1)])
    _raises(ValueError, FM, m.class_struggle, [('a', 'x' * 17, 1)])
    _raises(ValueError, XM, m.class_struggle, [('a', 'b', '1')])
    _raises(ValueError, XM, m.class_struggle, [('a', 'b', 0)])
    _raises(ValueError, XM, m.class_struggle, [('a', 'b', 10)])
    _raises(ValueError, XM, m.class_struggle, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: work must be a string of 1 to 16 characters',
            m.class_struggle, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: wealth must be a nonbool integer between 1 and 9',
            m.class_struggle, [('a', 'b', 1), ('c', 'd', 0)])
    # work is validated before faction, faction before wealth
    _raises(ValueError, WM, m.class_struggle, [('x' * 17, '', 0)])
    _raises(ValueError, FM, m.class_struggle, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.class_struggle, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.class_struggle((('a', 'b', 1),)) == m.class_struggle([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.class_struggle([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.class_struggle([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.class_struggle([('a', 'b', 1)] * 60)['total'] == 60
    assert m.class_struggle([('a', 'b', 9)])['gap'] == {'a': 0}
    # pre-seed pin: fresh accumulators only
    assert m.class_struggle([('p', 'a', 9), ('q', 'a', 1), ('p', 'b', 2)]) == {
        'total': 3, 'gap': {'p': 7, 'q': 0}, 'polarized': ['p'],
        'egalitarian': ['q'], 'widest': 'p'}
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
        _raises(TypeError, P, m.class_struggle, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (work, faction, wealth) triple',
                m.class_struggle, [K(('a', 'b', 1))])
    _raises(ValueError, WM, m.class_struggle, [(S('a'), 'b', 1)])
    _raises(ValueError, FM, m.class_struggle, [('a', S('b'), 1)])
    _raises(ValueError, XM, m.class_struggle, [('a', 'b', I(1))])
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
    ('type(work) is not str', 'not isinstance(work, str)'),
    ('type(faction) is not str', 'not isinstance(faction, str)'),
    ('type(wealth) is not int', 'not isinstance(wealth, int)'),
    ('not 1 <= len(work) <= 16', 'not 1 <= len(work) <= 17'),
    ('not 1 <= len(faction) <= 16', 'not 1 <= len(faction) <= 17'),
    ('not 1 <= wealth <= 9', 'not 1 <= wealth <= 10'),
    ('        holdings[work][faction] += wealth',
     '        holdings[work][faction] += 1'),
    ('if richest is None or holdings[work][faction] > richest:',
     'if richest is None or holdings[work][faction] < richest:'),
    ('if poorest is None or holdings[work][faction] < poorest:',
     'if poorest is None or holdings[work][faction] > poorest:'),
    ('gap[work] = richest - poorest', 'gap[work] = poorest - richest'),
    ('if gap[work] >= 7', 'if gap[work] >= 8'),
    ('if gap[work] == 0', 'if gap[work] == 1'),
    ('    polarized = sorted(', '    polarized = list('),
    ('if widest is None or gap[work] > gap[widest]:',
     'if widest is None or gap[work] < gap[widest]:'),
    ("'polarized': polarized", "'polarized': egalitarian"),
    ("'total': len(rows)", "'total': len(gap)"),
    ('        work, faction, wealth = row',
     '        faction, work, wealth = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
