"""Mutation and oracle tests for extra_doc.swarm_robotics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_947_swarm_robotics.py',
                        'src/sugarcode/extra_doc/swarm_robotics.py')

with open(SRC_PATH) as _f:
    SRC = _f.read()


class _Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise _Timeout()


def _load_code(code):
    module = types.ModuleType('mutant')
    exec(compile(code, 'mutant', 'exec'), module.__dict__)
    return module


class LyingS:
    def __eq__(self, other):
        return True

    def __ne__(self, other):
        return False

    def __hash__(self):
        return hash('a')


class ListSub(list):
    pass


def _core(module):
    m = module
    # oracle seeded with row number 947
    assert m.broadcast([]) == {'total': 0, 'reached': [], 'depth': {},
                               'unreached': []}
    # chain: depth accumulates hop by hop
    r = m.broadcast([('a', 'b'), ('b', 'c')])
    assert r == {'total': 2, 'reached': ['a', 'b', 'c'],
                 'depth': {'a': 0, 'b': 1, 'c': 2}, 'unreached': []}
    # diamond: shortest hop count wins (kills depth-first walks)
    r = m.broadcast([('a', 'b'), ('a', 'c'), ('b', 'd'), ('c', 'd')])
    assert r['depth'] == {'a': 0, 'b': 1, 'c': 1, 'd': 2}
    # separate team stays unreached
    r = m.broadcast([('a', 'b'), ('x', 'y')])
    assert r['reached'] == ['a', 'b'] and r['unreached'] == ['x', 'y']
    assert r['depth'] == {'a': 0, 'b': 1}
    # the source is the first sender, not the first receiver
    r = m.broadcast([('a', 'b'), ('b', 'c'), ('z', 'a')])
    assert r['depth'] == {'a': 0, 'b': 1, 'c': 2} and r['unreached'] == ['z']
    # self-hop reaches only the sender
    r = m.broadcast([('a', 'a')])
    assert r['reached'] == ['a'] and r['depth'] == {'a': 0}
    # cycle does not revisit
    r = m.broadcast([('a', 'b'), ('b', 'a')])
    assert r['depth'] == {'a': 0, 'b': 1}
    # dynamic equal-string witness: equal senders share one adjacency
    dyn = ''.join(['a', '1'])
    r = m.broadcast([(dyn, 'b'), (''.join(['a', '1']), 'c')])
    assert r['depth'] == {'a1': 0, 'b': 1, 'c': 1}
    # wide star: 20 relays from one source, deterministic sort
    names = ['r%02d' % i for i in range(20)]
    r = m.broadcast([('src', n) for n in names])
    assert r['reached'] == sorted(['src'] + names)
    assert r['depth'] == dict([('src', 0)] + [(n, 1) for n in names])
    assert r['unreached'] == []
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.broadcast('nope')
    with pytest.raises(TypeError):
        m.broadcast(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.broadcast([('a', 'b')] * 101)
    with pytest.raises(TypeError):
        m.broadcast([('a', 'b'), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.broadcast([('a', 'b'), ('a',)])
    with pytest.raises(TypeError):
        m.broadcast([(1, 'b')])
    with pytest.raises(TypeError):
        m.broadcast([('a', 1)])
    with pytest.raises(TypeError):
        m.broadcast([(LyingS(), 'b')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.broadcast([('', 'b')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.broadcast([('abcdefghi', 'b')])
    # first bad row pins, mixed failure types
    try:
        m.broadcast([('ok', 'b'), ('ok', 'c'), (7, 'b')])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.broadcast([('ok', 'b'), ('ok', '')])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.broadcast({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.broadcast(ListSub([('a', 'b')]))
    with pytest.raises(TypeError):
        m.broadcast([ListSub(('a', 'b'))])
    # tuple rows accepted exactly like lists
    assert m.broadcast((('a', 'b'),)) == m.broadcast([('a', 'b')])
    # boundary acceptance pins
    assert m.broadcast([('abcdefgh', 'b')])['reached'] == ['abcdefgh', 'b']
    assert m.broadcast([('a', 'b')] * 100)['total'] == 100
    return True


def battery(module):
    _core(module)
    _late(module)
    return True


def _survives(old, new):
    assert SRC.count(old) >= 1, f'needle missing: {old!r}'
    mutant = SRC.replace(old, new, 1)
    try:
        compile(mutant, 'mutant', 'exec')
    except SyntaxError:
        return 'syntax'
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(5)
    try:
        module = _load_code(mutant)
        battery(module)
    except (Exception, pytest.fail.Exception):
        return 'dies'
    except BaseException:
        return 'dies'
    finally:
        signal.alarm(0)
    return 'survives'


MUTANTS = [
    ('depth[nxt] = depth[robot] + 1', 'depth[nxt] = depth[robot]'),
    ('depth[nxt] = depth[robot] + 1', 'depth[nxt] = depth[robot] + 2'),
    ('depth[source] = 0', 'depth[source] = 1'),
    ('source = edges[0][0]', 'source = edges[0][1]'),
    ('source = edges[0][0]', 'source = edges[-1][0]'),
    ('adjacency.setdefault(sender, []).append(receiver)',
     'adjacency.setdefault(receiver, []).append(sender)'),
    ('for robot in queue:', 'for robot in list(queue):'),
    ('queue = [source]', 'queue = []'),
    ('mentioned.add(sender)', 'mentioned.add(receiver)'),
    ('reached = sorted(depth)', 'reached = sorted(mentioned)'),
    ('unreached = sorted(name for name in mentioned if name not in depth)',
     'unreached = sorted(name for name in mentioned if name in depth)'),
    ("'total': len(rows)", "'total': len(depth)"),
    ('sender, receiver = row', 'receiver, sender = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(name) <= MAX_NAME', 'not 1 <= len(name) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 947, Swarm Robotics' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
