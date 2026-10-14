import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import agent_learning as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
EP = 'row 1: episode must be a string of 1 to 16 characters'
AG = 'row 1: agent must be a string of 1 to 16 characters'
RE = 'row 1: reward must be a nonbool integer between 1 and 9'


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
    assert section == ('gradient computation, reward modeling, '
                       'exploration strategy, convergence proofs, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: frontier tracking over supplied rewards'
    assert mod.NOT_CLAIMED == ('gradient computation', 'reward modeling',
                               'exploration strategy', 'convergence proofs',
                               'production readiness')


def _expected(rows):
    best = None
    seen = {}
    catches = {}
    for episode, agent, reward in rows:
        behind = best is not None and (agent not in seen or seen[agent] < best)
        if best is not None and reward == best and behind:
            catches[agent] = catches.get(agent, 0) + 1
        seen[agent] = reward
        best = reward if best is None else max(best, reward)
    leader = None
    if catches:
        top = max(catches.values())
        order = list(dict.fromkeys(agent for _, agent, _ in rows))
        leader = next(a for a in order if catches.get(a) == top)
    return {'total': len(rows), 'catches': catches,
            'frontier': best, 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1943
    assert m.catch_frontier([('e', 'a', 5), ('e', 'b', 3),
                             ('e', 'b', 5)]) == {
        'total': 3, 'catches': {'b': 1}, 'frontier': 5, 'leader': 'b'}
    # one row accepted with full expected output
    assert m.catch_frontier([('e', 'a', 5)]) == {
        'total': 1, 'catches': {}, 'frontier': 5, 'leader': None}
    # a new agent arriving at the frontier catches it
    assert m.catch_frontier([('e', 'a', 9), ('e', 'b', 9)]) == {
        'total': 2, 'catches': {'b': 1}, 'frontier': 9, 'leader': 'b'}
    # setting a new frontier is not a catch
    assert m.catch_frontier([('e', 'a', 1), ('e', 'a', 9)]) == {
        'total': 2, 'catches': {}, 'frontier': 9, 'leader': None}
    # the frontier holder re-matching its own mark is not a catch
    assert m.catch_frontier([('e', 'a', 9), ('e', 'a', 9)]) == {
        'total': 2, 'catches': {}, 'frontier': 9, 'leader': None}
    # catches measure the frontier as of that row
    assert m.catch_frontier([('e', 'a', 3), ('e', 'b', 3),
                             ('e', 'a', 9), ('e', 'c', 9)]) == {
        'total': 4, 'catches': {'b': 1, 'c': 1}, 'frontier': 9, 'leader': 'b'}
    # a leader tie goes to the first supplied agent, not the first catch
    assert m.catch_frontier([('e', 'z', 4), ('e', 'q', 2), ('e', 'q', 4),
                             ('e', 'z', 1), ('e', 'z', 4)]) == {
        'total': 5, 'catches': {'q': 1, 'z': 1}, 'frontier': 4, 'leader': 'z'}
    # non-ASCII agents follow the same rule
    assert m.catch_frontier([('e', 'Üser-9!', 6), ('e', 'q?7', 2),
                             ('e', 'q?7', 6)]) == {
        'total': 3, 'catches': {'q?7': 1}, 'frontier': 6, 'leader': 'q?7'}
    # one agent can catch repeatedly
    assert m.catch_frontier([('e', 'a', 2), ('e', 'b', 5), ('e', 'a', 5),
                             ('e', 'a', 1), ('e', 'a', 5)]) == {
        'total': 5, 'catches': {'a': 2}, 'frontier': 5, 'leader': 'a'}
    # the agent's own mark moves with every row
    assert m.catch_frontier([('e', 'a', 5), ('e', 'b', 5),
                             ('e', 'b', 5)]) == {
        'total': 3, 'catches': {'b': 1}, 'frontier': 5, 'leader': 'b'}
    # pre-seed pin: fresh accumulators only
    assert m.catch_frontier([('e', 'm', 1), ('e', 'n', 9),
                             ('e', 'm', 9)]) == {
        'total': 3, 'catches': {'m': 1}, 'frontier': 9, 'leader': 'm'}
    rng = random.Random(1943)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.catch_frontier(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.catch_frontier, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.catch_frontier, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.catch_frontier, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.catch_frontier, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected an (episode, agent, reward) triple',
            m.catch_frontier, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.catch_frontier, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.catch_frontier, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, EP, m.catch_frontier, [(1, 'b', 1)])
    _raises(ValueError, EP, m.catch_frontier, [('', 'b', 1)])
    _raises(ValueError, EP, m.catch_frontier, [('x' * 17, 'b', 1)])
    _raises(ValueError, AG, m.catch_frontier, [('a', 1, 1)])
    _raises(ValueError, AG, m.catch_frontier, [('a', '', 1)])
    _raises(ValueError, AG, m.catch_frontier, [('a', 'x' * 17, 1)])
    _raises(ValueError, RE, m.catch_frontier, [('a', 'b', '1')])
    _raises(ValueError, RE, m.catch_frontier, [('a', 'b', 0)])
    _raises(ValueError, RE, m.catch_frontier, [('a', 'b', 10)])
    _raises(ValueError, RE, m.catch_frontier, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: episode must be a string of 1 to 16 characters',
            m.catch_frontier, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: reward must be a nonbool integer between 1 and 9',
            m.catch_frontier, [('a', 'b', 1), ('c', 'd', 0)])
    # episode is validated before agent, agent before reward
    _raises(ValueError, EP, m.catch_frontier, [('x' * 17, '', 0)])
    _raises(ValueError, AG, m.catch_frontier, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.catch_frontier, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.catch_frontier((('a', 'b', 1),)) == m.catch_frontier([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.catch_frontier([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.catch_frontier([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.catch_frontier([('a', 'b', 1)] * 60)['total'] == 60
    assert m.catch_frontier([('a', 'b', 9)])['frontier'] == 9
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.catch_frontier([('x' * 16, 'b', 5)])['total'] == 1
    assert m.catch_frontier([('a', 'y' * 16, 5)])['total'] == 1
    assert m.catch_frontier([('a', 'b', 5),
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
        _raises(TypeError, P, m.catch_frontier, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected an (episode, agent, reward) triple',
                m.catch_frontier, [K(('a', 'b', 1))])
    _raises(ValueError, EP, m.catch_frontier, [(S('a'), 'b', 1)])
    _raises(ValueError, AG, m.catch_frontier, [('a', S('b'), 1)])
    _raises(ValueError, RE, m.catch_frontier, [('a', 'b', I(1))])
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
    ('type(episode) is not str', 'not isinstance(episode, str)'),
    ('type(agent) is not str', 'not isinstance(agent, str)'),
    ('type(reward) is not int', 'not isinstance(reward, int)'),
    ('not 1 <= len(episode) <= 16', 'not 1 <= len(episode) <= 17'),
    ('not 1 <= len(agent) <= 16', 'not 1 <= len(agent) <= 17'),
    ('not 1 <= reward <= 9', 'not 1 <= reward <= 10'),
    ('and reward == frontier', 'and reward >= frontier'),
    ('agent not in own or own[agent] < frontier',
     'agent not in own or own[agent] <= frontier'),
    ('agent not in own or own[agent] < frontier',
     'agent in own and own[agent] < frontier'),
    ('for agent in order:', 'for agent in catches:'),
    ('for agent in order:', 'for agent in sorted(order):'),
    ('        own[agent] = reward', '        own[agent] = 0'),
    ("'catches': catches", "'catches': {}"),
    ("'frontier': frontier", "'frontier': 0"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(catches)"),
    ('        episode, agent, reward = row',
     '        agent, episode, reward = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
