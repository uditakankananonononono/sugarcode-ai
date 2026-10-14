import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ai_governance as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
FR = 'row 1: framework must be a string of 1 to 16 characters'
RE = 'row 1: region must be a string of 1 to 16 characters'
LE = 'row 1: level must be a nonbool integer between 1 and 9'


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
    assert section == ('framework drafting, jurisdiction mapping, '
                       'enforcement modeling, treaty analysis, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: cover counting over supplied levels'
    assert mod.NOT_CLAIMED == ('framework drafting', 'jurisdiction mapping',
                               'enforcement modeling', 'treaty analysis',
                               'production readiness')


def _expected(rows):
    regions = {}
    for framework, region, _level in rows:
        regions.setdefault(framework, set()).add(region)
    covers = {}
    covered = set()
    for f, mine in regions.items():
        for o, theirs in regions.items():
            if o != f and theirs < mine:
                covers[f] = covers.get(f, 0) + 1
                covered.add(o)
    leader = None
    if covers:
        most = max(covers.values())
        supply = list(dict.fromkeys(f for f, _r, _l in rows))
        leader = next(f for f in supply if covers.get(f) == most)
    independent = sorted(f for f in regions
                         if f not in covers and f not in covered)
    return {'total': len(rows), 'covers': covers,
            'count': sum(covers.values()),
            'independent': independent, 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1954
    assert m.count_covers([('f1', 'r1', 5), ('f1', 'r2', 5),
                           ('f2', 'r1', 5), ('f3', 'r3', 5)]) == {
        'total': 4, 'covers': {'f1': 1}, 'count': 1,
        'independent': ['f3'], 'leader': 'f1'}
    # one row accepted with full expected output
    assert m.count_covers([('f', 'r', 5)]) == {
        'total': 1, 'covers': {}, 'count': 0, 'independent': ['f'],
        'leader': None}
    # identical region sets cover nothing either way
    assert m.count_covers([('a', 'r', 5), ('b', 'r', 9)]) == {
        'total': 2, 'covers': {}, 'count': 0,
        'independent': ['a', 'b'], 'leader': None}
    # covers chain through nested region sets
    assert m.count_covers([('f1', 'r1', 5), ('f1', 'r2', 5),
                           ('f1', 'r3', 5), ('f2', 'r1', 5),
                           ('f2', 'r2', 5), ('f3', 'r1', 5)]) == {
        'total': 6, 'covers': {'f1': 2, 'f2': 1}, 'count': 3,
        'independent': [], 'leader': 'f1'}
    # the level never shapes a region set
    assert m.count_covers([('f1', 'r1', 1), ('f1', 'r2', 9),
                           ('f2', 'r1', 5)]) == {
        'total': 3, 'covers': {'f1': 1}, 'count': 1,
        'independent': [], 'leader': 'f1'}
    # non-ASCII frameworks follow the same rule
    assert m.count_covers([('fÜ', 'r1', 5), ('fÜ', 'r2', 5),
                           ('fX', 'r1', 5)]) == {
        'total': 3, 'covers': {'fÜ': 1}, 'count': 1,
        'independent': [], 'leader': 'fÜ'}
    # independent frameworks come back sorted, not in supply order
    assert m.count_covers([('zb', 'r1', 5), ('za', 'r9', 5)]) == {
        'total': 2, 'covers': {}, 'count': 0,
        'independent': ['za', 'zb'], 'leader': None}
    # repeated region rows never double count
    assert m.count_covers([('f1', 'r1', 5), ('f1', 'r1', 7),
                           ('f2', 'r1', 5)]) == {
        'total': 3, 'covers': {}, 'count': 0,
        'independent': ['f1', 'f2'], 'leader': None}
    # a leader tie goes to the first supplied framework
    assert m.count_covers([('z2', 'r1', 5), ('z2', 'r2', 5),
                           ('a2', 'r3', 5), ('a2', 'r4', 5),
                           ('z1', 'r1', 5), ('a1', 'r3', 5)]) == {
        'total': 6, 'covers': {'z2': 1, 'a2': 1}, 'count': 2,
        'independent': [], 'leader': 'z2'}
    # pre-seed pin: fresh accumulators only
    assert m.count_covers([('x', 'r1', 5), ('x', 'r2', 5),
                           ('y', 'r1', 5)]) == {
        'total': 3, 'covers': {'x': 1}, 'count': 1,
        'independent': [], 'leader': 'x'}
    rng = random.Random(1954)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_covers(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_covers, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_covers, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_covers, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_covers, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (framework, region, level) triple',
            m.count_covers, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_covers, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_covers, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, FR, m.count_covers, [(1, 'b', 1)])
    _raises(ValueError, FR, m.count_covers, [('', 'b', 1)])
    _raises(ValueError, FR, m.count_covers, [('x' * 17, 'b', 1)])
    _raises(ValueError, RE, m.count_covers, [('a', 1, 1)])
    _raises(ValueError, RE, m.count_covers, [('a', '', 1)])
    _raises(ValueError, RE, m.count_covers, [('a', 'x' * 17, 1)])
    _raises(ValueError, LE, m.count_covers, [('a', 'b', '1')])
    _raises(ValueError, LE, m.count_covers, [('a', 'b', 0)])
    _raises(ValueError, LE, m.count_covers, [('a', 'b', 10)])
    _raises(ValueError, LE, m.count_covers, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError,
            'row 3: framework must be a string of 1 to 16 characters',
            m.count_covers, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: level must be a nonbool integer between 1 and 9',
            m.count_covers, [('a', 'b', 1), ('c', 'd', 0)])
    # framework is validated before region, region before level
    _raises(ValueError, FR, m.count_covers, [('x' * 17, '', 0)])
    _raises(ValueError, RE, m.count_covers, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_covers,
            {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_covers((('a', 'b', 1),)) == m.count_covers([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_covers([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_covers([['a', 'x', 2], ('b', 'y', 1),
                                    ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_covers([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_covers([('a', 'b', 9)])['covers'] == {}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_covers([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_covers([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_covers([('a', 'b', 5),
                           ('x' * 16, 'y' * 16, 5)])['total'] == 2
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
        _raises(TypeError, P, m.count_covers, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (framework, region, level) triple',
                m.count_covers, [K(('a', 'b', 1))])
    _raises(ValueError, FR, m.count_covers, [(S('a'), 'b', 1)])
    _raises(ValueError, RE, m.count_covers, [('a', S('b'), 1)])
    _raises(ValueError, LE, m.count_covers, [('a', 'b', I(1))])
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
    ('type(framework) is not str', 'not isinstance(framework, str)'),
    ('type(region) is not str', 'not isinstance(region, str)'),
    ('type(level) is not int', 'not isinstance(level, int)'),
    ('not 1 <= len(framework) <= 16', 'not 1 <= len(framework) <= 17'),
    ('not 1 <= len(region) <= 16', 'not 1 <= len(region) <= 17'),
    ('not 1 <= level <= 9', 'not 1 <= level <= 10'),
    ('if other == framework:', 'if other != framework:'),
    ('< len(regions[framework])', '<= len(regions[framework])'),
    ('if region not in regions[framework]:',
     'if region in regions[framework]:'),
    ('covers[framework] += 1', 'covers[framework] += 2'),
    ('total += 1', 'total += 2'),
    ('framework not in covers and framework not in covered',
     'framework not in covers or framework not in covered'),
    ('for framework in order:', 'for framework in sorted(order):'),
    ("'independent': sorted(independent)", "'independent': independent"),
    ("'covers': covers", "'covers': {}"),
    ("'count': total", "'count': 0"),
    ("'independent': sorted(independent)", "'independent': []"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(covers)"),
    ('        framework, region, level = row',
     '        region, framework, level = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
