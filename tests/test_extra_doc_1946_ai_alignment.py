import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ai_alignment as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
GO = 'row 1: goal must be a string of 1 to 16 characters'
AG = 'row 1: agent must be a string of 1 to 16 characters'
DR = 'row 1: drift must be a nonbool integer between 1 and 9'


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
    assert section == ('goal specification, reward hacking, '
                       'interpretability, debate protocols, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: correction counting over supplied drift'
    assert mod.NOT_CLAIMED == ('goal specification', 'reward hacking',
                               'interpretability', 'debate protocols',
                               'production readiness')


def _expected(rows):
    flags = {}
    counts = {}
    for goal, agent, drift in rows:
        hot = flags.get(agent, False)
        if drift > 1:
            hot = True
        elif hot:
            counts[agent] = counts.get(agent, 0) + 1
            hot = False
        flags[agent] = hot
    pending = sorted(a for a in flags if flags[a])
    leader = None
    if counts:
        top = max(counts.values())
        order = list(dict.fromkeys(agent for _, agent, _ in rows))
        leader = next(a for a in order if counts.get(a) == top)
    return {'total': len(rows), 'corrections': counts,
            'pending': pending, 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1946
    assert m.count_corrections([('g', 'a', 5), ('g', 'a', 1)]) == {
        'total': 2, 'corrections': {'a': 1}, 'pending': [], 'leader': 'a'}
    # one row accepted with full expected output
    assert m.count_corrections([('g', 'x', 1)]) == {
        'total': 1, 'corrections': {}, 'pending': [], 'leader': None}
    # a raised flag with no correction stays pending
    assert m.count_corrections([('g', 'x', 5)]) == {
        'total': 1, 'corrections': {}, 'pending': ['x'], 'leader': None}
    # the flag survives more drift until a correction consumes it
    assert m.count_corrections([('g', 'a', 5), ('g', 'a', 3),
                                ('g', 'a', 1)]) == {
        'total': 3, 'corrections': {'a': 1}, 'pending': [], 'leader': 'a'}
    # a correction consumes the flag
    assert m.count_corrections([('g', 'a', 5), ('g', 'a', 1),
                                ('g', 'a', 1)]) == {
        'total': 3, 'corrections': {'a': 1}, 'pending': [], 'leader': 'a'}
    # pending agents come back sorted
    assert m.count_corrections([('g', 'z', 2), ('g', 'a', 2)]) == {
        'total': 2, 'corrections': {}, 'pending': ['a', 'z'], 'leader': None}
    # one agent can correct repeatedly
    assert m.count_corrections([('g', 'a', 5), ('g', 'a', 1),
                                ('g', 'a', 2), ('g', 'a', 1)]) == {
        'total': 4, 'corrections': {'a': 2}, 'pending': [], 'leader': 'a'}
    # a leader tie goes to the first supplied agent, not the first correction
    assert m.count_corrections([('g', 'b', 3), ('g', 'a', 5),
                                ('g', 'a', 1), ('g', 'b', 1)]) == {
        'total': 4, 'corrections': {'a': 1, 'b': 1},
        'pending': [], 'leader': 'b'}
    # non-ASCII agents follow the same rule
    assert m.count_corrections([('g', 'Üser-9!', 4), ('g', 'Üser-9!', 1),
                                ('g', 'q?7', 2)]) == {
        'total': 3, 'corrections': {'Üser-9!': 1},
        'pending': ['q?7'], 'leader': 'Üser-9!'}
    # flags are per agent, not global
    assert m.count_corrections([('g', 'a', 5), ('g', 'b', 1),
                                ('g', 'a', 1)]) == {
        'total': 3, 'corrections': {'a': 1}, 'pending': [], 'leader': 'a'}
    # a drift of 1 never raises
    assert m.count_corrections([('g', 'a', 1), ('g', 'a', 1)]) == {
        'total': 2, 'corrections': {}, 'pending': [], 'leader': None}
    # pre-seed pin: fresh accumulators only
    assert m.count_corrections([('g', 'm', 2), ('g', 'n', 1),
                                ('g', 'm', 1)]) == {
        'total': 3, 'corrections': {'m': 1}, 'pending': [], 'leader': 'm'}
    rng = random.Random(1946)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_corrections(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_corrections, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_corrections, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_corrections, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_corrections, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (goal, agent, drift) triple',
            m.count_corrections, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_corrections, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_corrections, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, GO, m.count_corrections, [(1, 'b', 1)])
    _raises(ValueError, GO, m.count_corrections, [('', 'b', 1)])
    _raises(ValueError, GO, m.count_corrections, [('x' * 17, 'b', 1)])
    _raises(ValueError, AG, m.count_corrections, [('a', 1, 1)])
    _raises(ValueError, AG, m.count_corrections, [('a', '', 1)])
    _raises(ValueError, AG, m.count_corrections, [('a', 'x' * 17, 1)])
    _raises(ValueError, DR, m.count_corrections, [('a', 'b', '1')])
    _raises(ValueError, DR, m.count_corrections, [('a', 'b', 0)])
    _raises(ValueError, DR, m.count_corrections, [('a', 'b', 10)])
    _raises(ValueError, DR, m.count_corrections, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: goal must be a string of 1 to 16 characters',
            m.count_corrections, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: drift must be a nonbool integer between 1 and 9',
            m.count_corrections, [('a', 'b', 1), ('c', 'd', 0)])
    # goal is validated before agent, agent before drift
    _raises(ValueError, GO, m.count_corrections, [('x' * 17, '', 0)])
    _raises(ValueError, AG, m.count_corrections, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_corrections, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_corrections((('a', 'b', 1),)) == m.count_corrections([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_corrections([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_corrections([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_corrections([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_corrections([('a', 'b', 9)])['pending'] == ['b']
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_corrections([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_corrections([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_corrections([('a', 'b', 5),
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
        _raises(TypeError, P, m.count_corrections, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (goal, agent, drift) triple',
                m.count_corrections, [K(('a', 'b', 1))])
    _raises(ValueError, GO, m.count_corrections, [(S('a'), 'b', 1)])
    _raises(ValueError, AG, m.count_corrections, [('a', S('b'), 1)])
    _raises(ValueError, DR, m.count_corrections, [('a', 'b', I(1))])
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
    ('type(goal) is not str', 'not isinstance(goal, str)'),
    ('type(agent) is not str', 'not isinstance(agent, str)'),
    ('type(drift) is not int', 'not isinstance(drift, int)'),
    ('not 1 <= len(goal) <= 16', 'not 1 <= len(goal) <= 17'),
    ('not 1 <= len(agent) <= 16', 'not 1 <= len(agent) <= 17'),
    ('not 1 <= drift <= 9', 'not 1 <= drift <= 10'),
    ('if drift > 1:', 'if drift >= 1:'),
    ('elif raised[agent]:', 'elif not raised[agent]:'),
    ('raised[agent] = True', 'raised[agent] = False'),
    ('            raised[agent] = False', '            raised[agent] = True'),
    ('corrections[agent] = corrections.get(agent, 0) + 1',
     'corrections[agent] = 1'),
    ("'pending': sorted(pending)", "'pending': pending"),
    ("'corrections': corrections", "'corrections': {}"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(corrections)"),
    ('        goal, agent, drift = row',
     '        agent, goal, drift = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
