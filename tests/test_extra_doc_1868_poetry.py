import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import poetry as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PM = 'row 1: poem must be a string of 1 to 16 characters'
LM = 'row 1: line must be a string of 1 to 16 characters'
RM = 'row 1: rhyme must be a nonbool integer between 1 and 9'


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
    assert section == ('real prosody, poetic merit, phonetic '
                       'analysis, compositional advice, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: couplet scanning over supplied rhyme classes'
    assert mod.NOT_CLAIMED == ('real prosody', 'poetic merit',
                               'phonetic analysis',
                               'compositional advice',
                               'production readiness')


def _expected(rows):
    lines = {}
    couplets = {}
    previous = {}
    for poem, line, rhyme in rows:
        if poem not in lines:
            lines[poem] = 0
        lines[poem] += 1
        if poem not in couplets:
            couplets[poem] = 0
        if poem in previous and previous[poem] == rhyme:
            couplets[poem] += 1
        previous[poem] = rhyme
    unrhymed = sorted(p for p in lines
                      if lines[p] >= 2 and couplets[p] == 0)
    richest = None
    for poem in couplets:
        if richest is None or couplets[poem] > couplets[richest]:
            richest = poem
    return {'total': len(rows), 'lines': lines, 'couplets': couplets,
            'unrhymed': unrhymed, 'richest': richest}


def _core(m):
    # fixed pins, oracle seeded with row number 1868
    assert m.scan_couplets([('p1', 'l1', 1), ('p1', 'l2', 1),
                            ('p1', 'l3', 2), ('p2', 'l1', 3),
                            ('p2', 'l2', 4), ('p3', 'l1', 5)]) == {
        'total': 6, 'lines': {'p1': 3, 'p2': 2, 'p3': 1},
        'couplets': {'p1': 1, 'p2': 0, 'p3': 0},
        'unrhymed': ['p2'], 'richest': 'p1'}
    # one line: no couplets, not unrhymed
    assert m.scan_couplets([('p', 'a', 1)]) == {
        'total': 1, 'lines': {'p': 1}, 'couplets': {'p': 0},
        'unrhymed': [], 'richest': 'p'}
    # three equal lines make two couplets
    r = m.scan_couplets([('p', 'a', 1), ('p', 'b', 1), ('p', 'c', 1)])
    assert r['couplets'] == {'p': 2}
    # the first line never pairs with anything before it
    r = m.scan_couplets([('p', 'a', 5), ('p', 'b', 5)])
    assert r['couplets'] == {'p': 1}
    # a broken run counts nothing
    r = m.scan_couplets([('p', 'a', 1), ('p', 'b', 2), ('p', 'c', 1)])
    assert r['couplets'] == {'p': 0} and r['unrhymed'] == ['p']
    # interleaved poems keep separate runs
    r = m.scan_couplets([('a', 'x', 1), ('b', 'y', 1), ('a', 'z', 1)])
    assert r['couplets'] == {'a': 1, 'b': 0}
    # two lines with different rhymes are unrhymed
    r = m.scan_couplets([('p', 'a', 1), ('p', 'b', 2)])
    assert r['unrhymed'] == ['p']
    # one line is never unrhymed
    r = m.scan_couplets([('p', 'a', 1)])
    assert r['unrhymed'] == []
    # the richest tie goes to the first supplied
    r = m.scan_couplets([('a', 'x', 1), ('a', 'y', 1),
                         ('b', 'w', 2), ('b', 'z', 2)])
    assert r['richest'] == 'a'
    # a strictly richer poem replaces the richest
    r = m.scan_couplets([('a', 'x', 1), ('a', 'y', 1),
                         ('b', 'w', 2), ('b', 'z', 2), ('b', 'v', 2)])
    assert r['richest'] == 'b'
    # unrhymed is sorted
    r = m.scan_couplets([('z', 'a', 1), ('z', 'b', 2),
                         ('a', 'c', 3), ('a', 'd', 4),
                         ('m', 'e', 5), ('m', 'f', 5)])
    assert r['unrhymed'] == ['a', 'z']
    # dicts keep first-touch order
    r = m.scan_couplets([('b', 'x', 1), ('a', 'y', 2)])
    assert r['lines'] == {'b': 1, 'a': 1}
    # non-ASCII poems follow the same rule
    r = m.scan_couplets([('Üser-9!', 'Ω-1', 7), ('Üser-9!', 'q?7', 7)])
    assert r == {'total': 2, 'lines': {'Üser-9!': 2},
                 'couplets': {'Üser-9!': 1}, 'unrhymed': [],
                 'richest': 'Üser-9!'}
    rng = random.Random(1868)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.scan_couplets(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.scan_couplets, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.scan_couplets, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.scan_couplets, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.scan_couplets, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (poem, line, rhyme) triple',
            m.scan_couplets, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.scan_couplets, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.scan_couplets, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PM, m.scan_couplets, [(1, 'b', 1)])
    _raises(ValueError, PM, m.scan_couplets, [('', 'b', 1)])
    _raises(ValueError, PM, m.scan_couplets, [('x' * 17, 'b', 1)])
    _raises(ValueError, LM, m.scan_couplets, [('a', 1, 1)])
    _raises(ValueError, LM, m.scan_couplets, [('a', '', 1)])
    _raises(ValueError, LM, m.scan_couplets, [('a', 'x' * 17, 1)])
    _raises(ValueError, RM, m.scan_couplets, [('a', 'b', '1')])
    _raises(ValueError, RM, m.scan_couplets, [('a', 'b', 0)])
    _raises(ValueError, RM, m.scan_couplets, [('a', 'b', 10)])
    _raises(ValueError, RM, m.scan_couplets, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: poem must be a string of 1 to 16 characters',
            m.scan_couplets, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: rhyme must be a nonbool integer between 1 and 9',
            m.scan_couplets, [('a', 'b', 1), ('c', 'd', 0)])
    # poem is validated before line, line before rhyme
    _raises(ValueError, PM, m.scan_couplets, [('x' * 17, '', 0)])
    _raises(ValueError, LM, m.scan_couplets, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.scan_couplets, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.scan_couplets((('a', 'b', 1),)) == m.scan_couplets([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.scan_couplets([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.scan_couplets([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.scan_couplets([('a', 'b', 1)] * 60)['total'] == 60
    assert m.scan_couplets([('a', 'b', 9)])['couplets'] == {'a': 0}
    # pre-seed pin: fresh accumulators only
    assert m.scan_couplets([('a', 'x', 1), ('b', 'y', 2), ('a', 'z', 1)]) == {
        'total': 3, 'lines': {'a': 2, 'b': 1},
        'couplets': {'a': 1, 'b': 0}, 'unrhymed': [], 'richest': 'a'}
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
        _raises(TypeError, P, m.scan_couplets, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (poem, line, rhyme) triple',
                m.scan_couplets, [K(('a', 'b', 1))])
    _raises(ValueError, PM, m.scan_couplets, [(S('a'), 'b', 1)])
    _raises(ValueError, LM, m.scan_couplets, [('a', S('b'), 1)])
    _raises(ValueError, RM, m.scan_couplets, [('a', 'b', I(1))])
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
    ('type(poem) is not str', 'not isinstance(poem, str)'),
    ('type(line) is not str', 'not isinstance(line, str)'),
    ('type(rhyme) is not int', 'not isinstance(rhyme, int)'),
    ('not 1 <= len(poem) <= 16', 'not 1 <= len(poem) <= 17'),
    ('not 1 <= len(line) <= 16', 'not 1 <= len(line) <= 17'),
    ('not 1 <= rhyme <= 9', 'not 1 <= rhyme <= 10'),
    ('        lines[poem] += 1', '        lines[poem] += 0'),
    ('        if poem in previous and previous[poem] == rhyme:',
     '        if poem in previous and previous[poem] != rhyme:'),
    ('            couplets[poem] += 1', '            couplets[poem] += 2'),
    ('        previous[poem] = rhyme', '        previous[poem] = 0'),
    ('if lines[p] >= 2 and couplets[p] == 0',
     'if lines[p] >= 1 and couplets[p] == 0'),
    ('if richest is None or couplets[poem] > couplets[richest]:',
     'if richest is None or couplets[poem] < couplets[richest]:'),
    ("'unrhymed': unrhymed", "'unrhymed': []"),
    ("'total': len(rows)", "'total': len(lines)"),
    ('        poem, line, rhyme = row',
     '        line, poem, rhyme = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
