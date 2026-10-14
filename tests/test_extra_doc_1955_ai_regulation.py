import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ai_regulation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
AC = 'row 1: act must be a string of 1 to 16 characters'
SE = 'row 1: section must be a string of 1 to 16 characters'
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
    assert section == ('statutory interpretation, enforcement prediction, '
                       'penalty modeling, jurisdictional reach, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: custody counting over supplied levels'
    assert mod.NOT_CLAIMED == ('statutory interpretation',
                               'enforcement prediction',
                               'penalty modeling', 'jurisdictional reach',
                               'production readiness')


def _expected(rows):
    peak = {}
    for act, section, level in rows:
        slot = peak.setdefault(section, {})
        slot[act] = max(level, slot.get(act, 0))
    custodies = {}
    contested = []
    for section, slot in peak.items():
        top = max(slot.values())
        holders = [a for a, v in slot.items() if v == top]
        if len(holders) == 1:
            custodies[holders[0]] = custodies.get(holders[0], 0) + 1
        else:
            contested.append(section)
    leader = None
    if custodies:
        most = max(custodies.values())
        supply = list(dict.fromkeys(a for a, _s, _l in rows))
        leader = next(a for a in supply if custodies.get(a) == most)
    return {'total': len(rows), 'custodies': custodies,
            'count': sum(custodies.values()),
            'contested': sorted(contested), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1955
    assert m.count_custodies([('a1', 's1', 9), ('a2', 's1', 5),
                              ('a1', 's2', 3), ('a2', 's2', 9)]) == {
        'total': 4, 'custodies': {'a1': 1, 'a2': 1}, 'count': 2,
        'contested': [], 'leader': 'a1'}
    # one row accepted with full expected output
    assert m.count_custodies([('a', 's', 5)]) == {
        'total': 1, 'custodies': {'a': 1}, 'count': 1,
        'contested': [], 'leader': 'a'}
    # a section tied at the peak is contested
    assert m.count_custodies([('a', 's', 9), ('b', 's', 9)]) == {
        'total': 2, 'custodies': {}, 'count': 0,
        'contested': ['s'], 'leader': None}
    # a re-scored act keeps its section peak
    assert m.count_custodies([('a', 's', 3), ('a', 's', 9),
                              ('b', 's', 8)]) == {
        'total': 3, 'custodies': {'a': 1}, 'count': 1,
        'contested': [], 'leader': 'a'}
    # a third act below a tied peak changes nothing
    assert m.count_custodies([('a', 's', 9), ('b', 's', 9),
                              ('c', 's', 4)]) == {
        'total': 3, 'custodies': {}, 'count': 0,
        'contested': ['s'], 'leader': None}
    # contested sections come back sorted, not in supply order
    assert m.count_custodies([('x', 's2', 9), ('y', 's2', 9),
                              ('x', 's1', 8), ('y', 's1', 8)]) == {
        'total': 4, 'custodies': {}, 'count': 0,
        'contested': ['s1', 's2'], 'leader': None}
    # non-ASCII acts follow the same rule
    assert m.count_custodies([('fÜ', 's', 7), ('fX', 's', 3)]) == {
        'total': 2, 'custodies': {'fÜ': 1}, 'count': 1,
        'contested': [], 'leader': 'fÜ'}
    # a leader tie goes to the first supplied act
    assert m.count_custodies([('z', 's1', 9), ('a', 's1', 1),
                              ('a', 's2', 9), ('z', 's2', 1)]) == {
        'total': 4, 'custodies': {'z': 1, 'a': 1}, 'count': 2,
        'contested': [], 'leader': 'z'}
    # pre-seed pin: fresh accumulators only
    assert m.count_custodies([('m', 's1', 9), ('n', 's1', 1),
                              ('n', 's2', 9), ('m', 's2', 1)]) == {
        'total': 4, 'custodies': {'m': 1, 'n': 1}, 'count': 2,
        'contested': [], 'leader': 'm'}
    rng = random.Random(1955)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_custodies(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_custodies, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_custodies, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_custodies, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_custodies, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (act, section, level) triple',
            m.count_custodies, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_custodies, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_custodies, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, AC, m.count_custodies, [(1, 'b', 1)])
    _raises(ValueError, AC, m.count_custodies, [('', 'b', 1)])
    _raises(ValueError, AC, m.count_custodies, [('x' * 17, 'b', 1)])
    _raises(ValueError, SE, m.count_custodies, [('a', 1, 1)])
    _raises(ValueError, SE, m.count_custodies, [('a', '', 1)])
    _raises(ValueError, SE, m.count_custodies, [('a', 'x' * 17, 1)])
    _raises(ValueError, LE, m.count_custodies, [('a', 'b', '1')])
    _raises(ValueError, LE, m.count_custodies, [('a', 'b', 0)])
    _raises(ValueError, LE, m.count_custodies, [('a', 'b', 10)])
    _raises(ValueError, LE, m.count_custodies, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: act must be a string of 1 to 16 characters',
            m.count_custodies, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: level must be a nonbool integer between 1 and 9',
            m.count_custodies, [('a', 'b', 1), ('c', 'd', 0)])
    # act is validated before section, section before level
    _raises(ValueError, AC, m.count_custodies, [('x' * 17, '', 0)])
    _raises(ValueError, SE, m.count_custodies, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_custodies,
            {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_custodies((('a', 'b', 1),)) == m.count_custodies(
        [('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_custodies([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_custodies([['a', 'x', 2], ('b', 'y', 1),
                                       ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_custodies([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_custodies([('a', 'b', 9)])['custodies'] == {'a': 1}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_custodies([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_custodies([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_custodies([('a', 'b', 5),
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
        _raises(TypeError, P, m.count_custodies, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (act, section, level) triple',
                m.count_custodies, [K(('a', 'b', 1))])
    _raises(ValueError, AC, m.count_custodies, [(S('a'), 'b', 1)])
    _raises(ValueError, SE, m.count_custodies, [('a', S('b'), 1)])
    _raises(ValueError, LE, m.count_custodies, [('a', 'b', I(1))])
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
    ('type(act) is not str', 'not isinstance(act, str)'),
    ('type(section) is not str', 'not isinstance(section, str)'),
    ('type(level) is not int', 'not isinstance(level, int)'),
    ('not 1 <= len(act) <= 16', 'not 1 <= len(act) <= 17'),
    ('not 1 <= len(section) <= 16', 'not 1 <= len(section) <= 17'),
    ('not 1 <= level <= 9', 'not 1 <= level <= 10'),
    ('level > per_section[section][act]',
     'level < per_section[section][act]'),
    ('top = max(slot.values())', 'top = min(slot.values())'),
    ('if slot[act] == top:', 'if slot[act] < top:'),
    ('if len(holders) == 1:', 'if len(holders) != 1:'),
    ('custodies[only] += 1', 'custodies[only] += 2'),
    ('count += 1', 'count += 2'),
    ('for act in order:', 'for act in sorted(order):'),
    ("'contested': sorted(contested)", "'contested': contested"),
    ("'custodies': custodies", "'custodies': {}"),
    ("'count': count", "'count': 0"),
    ("'contested': sorted(contested)", "'contested': []"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(custodies)"),
    ('        act, section, level = row',
     '        section, act, level = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
