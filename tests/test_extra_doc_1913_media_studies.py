import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import media_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
ST = 'row 1: story must be a string of 1 to 16 characters'
OU = 'row 1: outlet must be a string of 1 to 16 characters'
RA = 'row 1: reach must be a nonbool integer between 1 and 9'


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
    assert section == ('journalism ethics, audience measurement, '
                       'advertising, media law, production readiness.')
    assert mod.SCOPE == 'PARTIAL: story mapping over supplied reaches'
    assert mod.NOT_CLAIMED == ('journalism ethics', 'audience measurement',
                               'advertising', 'media law',
                               'production readiness')


def _expected(rows):
    carriers = {}
    leads = {}
    for story, outlet, reach in rows:
        if story not in carriers:
            carriers[story] = {}
        if outlet not in carriers[story] or reach > carriers[story][outlet]:
            carriers[story][outlet] = reach
        if story in leads:
            if reach > carriers[story][leads[story]]:
                leads[story] = outlet
        else:
            leads[story] = outlet
    counts = {}
    for story in carriers:
        counts[story] = len(carriers[story])
    syndicated = sorted(s for s in counts if counts[s] >= 2)
    exclusive = set()
    for story in carriers:
        if counts[story] == 1:
            for outlet in carriers[story]:
                exclusive.add(outlet)
    out_leads = {}
    for story in syndicated:
        out_leads[story] = leads[story]
    return {'total': len(rows), 'carriers': counts,
            'syndicated': syndicated, 'exclusive': sorted(exclusive),
            'leads': out_leads}


def _core(m):
    # fixed pins, oracle seeded with row number 1913
    assert m.map_stories([('st1', 'north', 9), ('st1', 'south', 3),
                          ('st2', 'north', 5), ('st3', 'south', 1),
                          ('st3', 'east', 2), ('st3', 'west', 4)]) == {
        'total': 6, 'carriers': {'st1': 2, 'st2': 1, 'st3': 3},
        'syndicated': ['st1', 'st3'], 'exclusive': ['north'],
        'leads': {'st1': 'north', 'st3': 'west'}}
    # one story, one outlet: nothing syndicated, the outlet is exclusive
    assert m.map_stories([('s', 'o', 5)]) == {
        'total': 1, 'carriers': {'s': 1}, 'syndicated': [],
        'exclusive': ['o'], 'leads': {}}
    # every story shared means no exclusive outlet
    r = m.map_stories([('a', 'x', 1), ('a', 'y', 1),
                       ('b', 'x', 1), ('b', 'y', 1)])
    assert r['carriers'] == {'a': 2, 'b': 2} and r['exclusive'] == []
    assert r['leads'] == {'a': 'x', 'b': 'x'}
    # the lead tie goes to the first supplied row
    assert m.map_stories([('a', 'y', 2), ('a', 'x', 2)])['leads'] == {'a': 'y'}
    # repeat rows from one outlet keep its best reach
    r = m.map_stories([('s', 'o', 3), ('s', 'o', 7), ('s', 'p', 1)])
    assert r == {'total': 3, 'carriers': {'s': 2}, 'syndicated': ['s'],
                 'exclusive': [], 'leads': {'s': 'o'}}
    # dicts keep first-touch order, lists sort by codepoint
    r = m.map_stories([('s', 'z', 1), ('t', 'a', 2)])
    assert r['carriers'] == {'s': 1, 't': 1} and r['exclusive'] == ['a', 'z']
    # non-ASCII stories and outlets follow the same rule
    r = m.map_stories([('Üser-9!', 'Ω-1', 2), ('q?7', 'Ω-1', 8),
                       ('q?7', 'Üser-9!', 8)])
    assert r == {'total': 3, 'carriers': {'Üser-9!': 1, 'q?7': 2},
                 'syndicated': ['q?7'], 'exclusive': ['Ω-1'],
                 'leads': {'q?7': 'Ω-1'}}
    # pre-seed pin: fresh accumulators only
    assert m.map_stories([('s', 'p', 8), ('t', 'p', 7),
                          ('s', 'q', 3), ('u', 'r', 5)]) == {
        'total': 4, 'carriers': {'s': 2, 't': 1, 'u': 1},
        'syndicated': ['s'], 'exclusive': ['p', 'r'], 'leads': {'s': 'p'}}
    rng = random.Random(1913)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.map_stories(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.map_stories, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.map_stories, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.map_stories, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.map_stories, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (story, outlet, reach) triple',
            m.map_stories, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.map_stories, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.map_stories, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, ST, m.map_stories, [(1, 'b', 1)])
    _raises(ValueError, ST, m.map_stories, [('', 'b', 1)])
    _raises(ValueError, ST, m.map_stories, [('x' * 17, 'b', 1)])
    _raises(ValueError, OU, m.map_stories, [('a', 1, 1)])
    _raises(ValueError, OU, m.map_stories, [('a', '', 1)])
    _raises(ValueError, OU, m.map_stories, [('a', 'x' * 17, 1)])
    _raises(ValueError, RA, m.map_stories, [('a', 'b', '1')])
    _raises(ValueError, RA, m.map_stories, [('a', 'b', 0)])
    _raises(ValueError, RA, m.map_stories, [('a', 'b', 10)])
    _raises(ValueError, RA, m.map_stories, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: story must be a string of 1 to 16 characters',
            m.map_stories, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: reach must be a nonbool integer between 1 and 9',
            m.map_stories, [('a', 'b', 1), ('c', 'd', 0)])
    # story is validated before outlet, outlet before reach
    _raises(ValueError, ST, m.map_stories, [('x' * 17, '', 0)])
    _raises(ValueError, OU, m.map_stories, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.map_stories, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.map_stories((('a', 'b', 1),)) == m.map_stories([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.map_stories([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.map_stories([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.map_stories([('a', 'b', 1)] * 60)['total'] == 60
    assert m.map_stories([('a', 'b', 9)])['carriers'] == {'a': 1}
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
        _raises(TypeError, P, m.map_stories, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (story, outlet, reach) triple',
                m.map_stories, [K(('a', 'b', 1))])
    _raises(ValueError, ST, m.map_stories, [(S('a'), 'b', 1)])
    _raises(ValueError, OU, m.map_stories, [('a', S('b'), 1)])
    _raises(ValueError, RA, m.map_stories, [('a', 'b', I(1))])
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
    ('type(story) is not str', 'not isinstance(story, str)'),
    ('type(outlet) is not str', 'not isinstance(outlet, str)'),
    ('type(reach) is not int', 'not isinstance(reach, int)'),
    ('not 1 <= len(story) <= 16', 'not 1 <= len(story) <= 17'),
    ('not 1 <= len(outlet) <= 16', 'not 1 <= len(outlet) <= 17'),
    ('not 1 <= reach <= 9', 'not 1 <= reach <= 10'),
    ('if outlet not in carriers[story] or reach > carriers[story][outlet]:',
     'if outlet not in carriers[story] or reach < carriers[story][outlet]:'),
    ('            if reach > carriers[story][leads[story]]:',
     '            if reach < carriers[story][leads[story]]:'),
    ('        counts[story] = len(carriers[story])',
     '        counts[story] = len(leads)'),
    ('if counts[s] >= 2', 'if counts[s] >= 3'),
    ('        if counts[story] == 1:', '        if counts[story] == 2:'),
    ("'carriers': counts", "'carriers': {}"),
    ("'syndicated': syndicated", "'syndicated': []"),
    ("'exclusive': sorted(exclusive)", "'exclusive': []"),
    ("'leads': out_leads", "'leads': leads"),
    ("'total': len(rows)", "'total': len(carriers)"),
    ('        story, outlet, reach = row', '        outlet, story, reach = row'),
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
    assert mod.map_stories([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.map_stories([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.map_stories([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
