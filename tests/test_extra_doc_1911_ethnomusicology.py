import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ethnomusicology as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SG = 'row 1: song must be a string of 1 to 16 characters'
RG = 'row 1: region must be a string of 1 to 16 characters'
LN = 'row 1: length must be a nonbool integer between 1 and 9'


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
    assert section == ('fieldwork, organology, transcription, '
                       'cultural ownership, production readiness.')
    assert mod.SCOPE == 'PARTIAL: region weighing over supplied lengths'
    assert mod.NOT_CLAIMED == ('fieldwork', 'organology', 'transcription',
                               'cultural ownership', 'production readiness')


def _expected(rows):
    totals = {}
    for song, region, length in rows:
        if region not in totals:
            totals[region] = 0
        totals[region] += length
    grand = sum(totals.values())
    majority = None
    for region in totals:
        if totals[region] > grand - totals[region]:
            majority = region
    fringe = sorted(r for r in totals if totals[r] <= 4)
    plurality = None
    for region in totals:
        if plurality is None or totals[region] > totals[plurality]:
            plurality = region
    return {'total': len(rows), 'totals': totals, 'majority': majority,
            'fringe': fringe, 'plurality': plurality}


def _core(m):
    # fixed pins, oracle seeded with row number 1911
    assert m.weigh_regions([('s1', 'north', 9), ('s2', 'north', 6),
                            ('s3', 'south', 2), ('s4', 'east', 3)]) == {
        'total': 4, 'totals': {'north': 15, 'south': 2, 'east': 3},
        'majority': 'north', 'fringe': ['east', 'south'],
        'plurality': 'north'}
    # a lone region always holds the majority
    assert m.weigh_regions([('s', 'r', 5)]) == {
        'total': 1, 'totals': {'r': 5}, 'majority': 'r',
        'fringe': [], 'plurality': 'r'}
    # an even split is no majority
    r = m.weigh_regions([('a', 'x', 5), ('b', 'y', 5)])
    assert r['majority'] is None and r['plurality'] == 'x'
    # a strict edge still majors: 6 over 5
    assert m.weigh_regions([('a', 'x', 6), ('b', 'y', 5)])['majority'] == 'x'
    # a total of exactly 4 is fringe, 5 is not
    assert m.weigh_regions([('s', 'r', 4)])['fringe'] == ['r']
    assert m.weigh_regions([('s', 'r', 5)])['fringe'] == []
    # a majority region can itself be fringe
    assert m.weigh_regions([('s', 'r', 4)])['majority'] == 'r'
    # the plurality tie goes to the first supplied region
    r = m.weigh_regions([('s', 'x', 7), ('t', 'y', 7)])
    assert r['plurality'] == 'x'
    # dicts keep first-touch order
    r = m.weigh_regions([('s', 'z', 1), ('t', 'a', 2)])
    assert r['totals'] == {'z': 1, 'a': 2} and r['fringe'] == ['a', 'z']
    # non-ASCII regions follow the same rule
    r = m.weigh_regions([('s', 'Üser-9!', 9), ('t', 'q?7', 1)])
    assert r == {'total': 2, 'totals': {'Üser-9!': 9, 'q?7': 1},
                 'majority': 'Üser-9!', 'fringe': ['q?7'],
                 'plurality': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.weigh_regions([('s', 'p', 8), ('t', 'p', 7), ('u', 'q', 3)]) == {
        'total': 3, 'totals': {'p': 15, 'q': 3}, 'majority': 'p',
        'fringe': ['q'], 'plurality': 'p'}
    rng = random.Random(1911)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.weigh_regions(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_regions, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_regions, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weigh_regions, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.weigh_regions, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (song, region, length) triple',
            m.weigh_regions, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.weigh_regions, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.weigh_regions, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SG, m.weigh_regions, [(1, 'b', 1)])
    _raises(ValueError, SG, m.weigh_regions, [('', 'b', 1)])
    _raises(ValueError, SG, m.weigh_regions, [('x' * 17, 'b', 1)])
    _raises(ValueError, RG, m.weigh_regions, [('a', 1, 1)])
    _raises(ValueError, RG, m.weigh_regions, [('a', '', 1)])
    _raises(ValueError, RG, m.weigh_regions, [('a', 'x' * 17, 1)])
    _raises(ValueError, LN, m.weigh_regions, [('a', 'b', '1')])
    _raises(ValueError, LN, m.weigh_regions, [('a', 'b', 0)])
    _raises(ValueError, LN, m.weigh_regions, [('a', 'b', 10)])
    _raises(ValueError, LN, m.weigh_regions, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: song must be a string of 1 to 16 characters',
            m.weigh_regions, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: length must be a nonbool integer between 1 and 9',
            m.weigh_regions, [('a', 'b', 1), ('c', 'd', 0)])
    # song is validated before region, region before length
    _raises(ValueError, SG, m.weigh_regions, [('x' * 17, '', 0)])
    _raises(ValueError, RG, m.weigh_regions, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.weigh_regions, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.weigh_regions((('a', 'b', 1),)) == m.weigh_regions([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.weigh_regions([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.weigh_regions([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.weigh_regions([('a', 'b', 1)] * 60)['total'] == 60
    assert m.weigh_regions([('a', 'b', 9)])['totals'] == {'b': 9}
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
        _raises(TypeError, P, m.weigh_regions, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (song, region, length) triple',
                m.weigh_regions, [K(('a', 'b', 1))])
    _raises(ValueError, SG, m.weigh_regions, [(S('a'), 'b', 1)])
    _raises(ValueError, RG, m.weigh_regions, [('a', S('b'), 1)])
    _raises(ValueError, LN, m.weigh_regions, [('a', 'b', I(1))])
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
    ('type(song) is not str', 'not isinstance(song, str)'),
    ('type(region) is not str', 'not isinstance(region, str)'),
    ('type(length) is not int', 'not isinstance(length, int)'),
    ('not 1 <= len(song) <= 16', 'not 1 <= len(song) <= 17'),
    ('not 1 <= len(region) <= 16', 'not 1 <= len(region) <= 17'),
    ('not 1 <= length <= 9', 'not 1 <= length <= 10'),
    ('        totals[region] += length', '        totals[region] += 1'),
    ('        if totals[region] > grand - totals[region]:',
     '        if totals[region] >= grand - totals[region]:'),
    ('    grand = sum(totals.values())', '    grand = len(totals)'),
    ('if totals[r] <= 4', 'if totals[r] <= 3'),
    ('if plurality is None or totals[region] > totals[plurality]:',
     'if plurality is None or totals[region] < totals[plurality]:'),
    ("'majority': majority", "'majority': plurality"),
    ("'fringe': fringe", "'fringe': []"),
    ("'totals': totals", "'totals': {}"),
    ("'total': len(rows)", "'total': len(totals)"),
    ('        song, region, length = row',
     '        region, song, length = row'),
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
    assert mod.weigh_regions([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.weigh_regions([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.weigh_regions([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
