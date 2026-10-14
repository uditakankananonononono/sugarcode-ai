import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import fair_ai as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
ME = 'row 1: metric must be a string of 1 to 16 characters'
GR = 'row 1: group must be a string of 1 to 16 characters'
VA = 'row 1: value must be a nonbool integer between 1 and 9'


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
    assert section == ('metric selection, bias auditing, '
                       'intersectional analysis, policy drafting, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: breakaway counting over supplied values'
    assert mod.NOT_CLAIMED == ('metric selection', 'bias auditing',
                               'intersectional analysis', 'policy drafting',
                               'production readiness')


def _expected(rows):
    latest = {}
    brk = {}
    for _metric, group, value in rows:
        others = [g for g in latest if g != group]
        multi = len(latest) >= 2 or (len(latest) == 1 and group not in latest)
        if multi and others and max(latest[g] for g in others) < value:
            brk[group] = brk.get(group, 0) + 1
        latest[group] = value
    leader = None
    if brk:
        top = max(brk.values())
        supply = list(dict.fromkeys(g for _m, g, _v in rows))
        leader = next(g for g in supply if brk.get(g) == top)
    return {'total': len(rows), 'breakaways': brk,
            'count': sum(brk.values()), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1951
    assert m.count_breakaways([('m', 'a', 5), ('m', 'b', 3),
                               ('m', 'a', 4), ('m', 'b', 9)]) == {
        'total': 4, 'breakaways': {'a': 1, 'b': 1}, 'count': 2,
        'leader': 'a'}
    # one row accepted with full expected output
    assert m.count_breakaways([('m', 'g', 5)]) == {
        'total': 1, 'breakaways': {}, 'count': 0, 'leader': None}
    # matching the only other latest is not a breakaway
    assert m.count_breakaways([('m', 'a', 5), ('m', 'b', 5)]) == {
        'total': 2, 'breakaways': {}, 'count': 0, 'leader': None}
    # a lone group can never break away from itself
    assert m.count_breakaways([('m', 'a', 9), ('m', 'a', 1),
                               ('m', 'a', 9)]) == {
        'total': 3, 'breakaways': {}, 'count': 0, 'leader': None}
    # a second group's first row is checked against the incumbent
    assert m.count_breakaways([('m', 'a', 5), ('m', 'b', 9)]) == {
        'total': 2, 'breakaways': {'b': 1}, 'count': 1, 'leader': 'b'}
    # the latest value moves with every row, breakaway or not
    assert m.count_breakaways([('m', 'a', 9), ('m', 'b', 8),
                               ('m', 'a', 1), ('m', 'b', 2)]) == {
        'total': 4, 'breakaways': {'b': 1}, 'count': 1, 'leader': 'b'}
    # a row must top every other group's latest
    assert m.count_breakaways([('m', 'a', 5), ('m', 'b', 3),
                               ('m', 'c', 4)]) == {
        'total': 3, 'breakaways': {}, 'count': 0, 'leader': None}
    assert m.count_breakaways([('m', 'a', 5), ('m', 'b', 3),
                               ('m', 'c', 4), ('m', 'd', 9)]) == {
        'total': 4, 'breakaways': {'d': 1}, 'count': 1, 'leader': 'd'}
    # the metric label does not split a group's latest
    assert m.count_breakaways([('m1', 'a', 5), ('m2', 'a', 9),
                               ('m1', 'b', 8)]) == {
        'total': 3, 'breakaways': {}, 'count': 0, 'leader': None}
    # non-ASCII groups follow the same rule
    assert m.count_breakaways([('m', 'Üser-9!', 2), ('m', 'q?7', 9)]) == {
        'total': 2, 'breakaways': {'q?7': 1}, 'count': 1,
        'leader': 'q?7'}
    # a leader tie goes to the first supplied group
    assert m.count_breakaways([('m', 'b', 5), ('m', 'a', 3),
                               ('m', 'a', 9), ('m', 'b', 8),
                               ('m', 'a', 1), ('m', 'b', 9)]) == {
        'total': 6, 'breakaways': {'a': 1, 'b': 1}, 'count': 2,
        'leader': 'b'}
    # pre-seed pin: fresh accumulators only
    assert m.count_breakaways([('m', 'x', 3), ('m', 'n', 9),
                               ('m', 'x', 1), ('m', 'n', 2)]) == {
        'total': 4, 'breakaways': {'n': 2}, 'count': 2, 'leader': 'n'}
    rng = random.Random(1951)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_breakaways(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_breakaways, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_breakaways, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_breakaways, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_breakaways, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (metric, group, value) triple',
            m.count_breakaways, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_breakaways, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_breakaways, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, ME, m.count_breakaways, [(1, 'b', 1)])
    _raises(ValueError, ME, m.count_breakaways, [('', 'b', 1)])
    _raises(ValueError, ME, m.count_breakaways, [('x' * 17, 'b', 1)])
    _raises(ValueError, GR, m.count_breakaways, [('a', 1, 1)])
    _raises(ValueError, GR, m.count_breakaways, [('a', '', 1)])
    _raises(ValueError, GR, m.count_breakaways, [('a', 'x' * 17, 1)])
    _raises(ValueError, VA, m.count_breakaways, [('a', 'b', '1')])
    _raises(ValueError, VA, m.count_breakaways, [('a', 'b', 0)])
    _raises(ValueError, VA, m.count_breakaways, [('a', 'b', 10)])
    _raises(ValueError, VA, m.count_breakaways, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: metric must be a string of 1 to 16 characters',
            m.count_breakaways, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: value must be a nonbool integer between 1 and 9',
            m.count_breakaways, [('a', 'b', 1), ('c', 'd', 0)])
    # metric is validated before group, group before value
    _raises(ValueError, ME, m.count_breakaways, [('x' * 17, '', 0)])
    _raises(ValueError, GR, m.count_breakaways, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_breakaways,
            {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_breakaways((('a', 'b', 1),)) == m.count_breakaways(
        [('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_breakaways([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_breakaways([['a', 'x', 2], ('b', 'y', 1),
                                        ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_breakaways([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_breakaways([('a', 'b', 9)])['breakaways'] == {}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_breakaways([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_breakaways([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_breakaways([('a', 'b', 5),
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
        _raises(TypeError, P, m.count_breakaways, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (metric, group, value) triple',
                m.count_breakaways, [K(('a', 'b', 1))])
    _raises(ValueError, ME, m.count_breakaways, [(S('a'), 'b', 1)])
    _raises(ValueError, GR, m.count_breakaways, [('a', S('b'), 1)])
    _raises(ValueError, VA, m.count_breakaways, [('a', 'b', I(1))])
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
    ('type(metric) is not str', 'not isinstance(metric, str)'),
    ('type(group) is not str', 'not isinstance(group, str)'),
    ('type(value) is not int', 'not isinstance(value, int)'),
    ('not 1 <= len(metric) <= 16', 'not 1 <= len(metric) <= 17'),
    ('not 1 <= len(group) <= 16', 'not 1 <= len(group) <= 17'),
    ('not 1 <= value <= 9', 'not 1 <= value <= 10'),
    ('value <= latest[other]', 'value < latest[other]'),
    ('value <= latest[other]', 'value >= latest[other]'),
    ('if other != group and', 'if other == group and'),
    ('len(latest) >= 2', 'len(latest) >= 3'),
    ('len(latest) == 1 and group not in latest', 'len(latest) == 1'),
    ('breakaways[group] += 1', 'breakaways[group] += 2'),
    ('        latest[group] = value', '        latest[group] = 0'),
    ('for group in order:', 'for group in sorted(order):'),
    ("'breakaways': breakaways", "'breakaways': {}"),
    ("'count': total", "'count': 0"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(breakaways)"),
    ('        metric, group, value = row',
     '        group, metric, value = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
