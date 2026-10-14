"""Mutation and oracle tests for extra_doc.epigenetic_robotics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_944_epigenetic_robotics.py',
                        'src/sugarcode/extra_doc/epigenetic_robotics.py')

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


class LyingI:
    def __index__(self):
        return 4


class ListSub(list):
    pass


def _core(module):
    m = module
    # oracle seeded with row number 944
    assert m.interact([]) == {'total': 0, 'crossed': {}, 'uncrossed': []}
    # signals 4 then 3: running 2, then 3 -> crosses exactly at step 2
    r = m.interact([('a', 4), ('a', 3)])
    assert r == {'total': 2, 'crossed': {'a': 2}, 'uncrossed': []}
    # decay pins: decay 1 would cross at step 1, no decay at step 1
    r = m.interact([('a', 4)])
    assert r['crossed'] == {} and r['uncrossed'] == ['a']
    # threshold pin: 4 then 3 reaches exactly 3; a higher bar never crosses
    r = m.interact([('a', 5), ('a', 5)])
    assert r['crossed'] == {'a': 1}  # delta 3 crosses immediately, then 6
    # interleaved robots keep separate running sums and step indices
    r = m.interact([('a', 4), ('b', 10), ('a', 3)])
    assert r['crossed'] == {'b': 2, 'a': 3}
    # first crossing step is kept, never overwritten
    r = m.interact([('a', 10), ('a', 10), ('a', 10)])
    assert r['crossed'] == {'a': 1}
    # a crossed robot that decays back below the bar stays crossed
    r = m.interact([('a', 10), ('a', 0), ('a', 0), ('a', 0)])
    assert r['crossed'] == {'a': 1} and r['uncrossed'] == []
    # neutral and negative signals never cross
    r = m.interact([('a', 2)])
    assert r['uncrossed'] == ['a']
    r = m.interact([('a', 0), ('a', 0)])
    assert r['uncrossed'] == ['a']
    # dynamic equal-string witness: equal names fold into one entry
    dyn = ''.join(['r', '1'])
    r = m.interact([(dyn, 4), (''.join(['r', '1']), 3)])
    assert r['crossed'] == {'r1': 2}
    # wide many-name sort pin (20 robots, deterministic)
    names = ['bot%02d' % i for i in range(20)]
    r = m.interact([(n, 1) for n in names])
    assert r['uncrossed'] == sorted(names)
    assert r['crossed'] == {}
    rows = [(n, 10) for n in names] + [(n, 10) for n in names]
    r = m.interact(rows)
    assert r['crossed'] == {n: i + 1 for i, n in enumerate(names)}
    assert r['total'] == 40
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.interact('nope')
    with pytest.raises(TypeError):
        m.interact(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.interact([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.interact([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.interact([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.interact([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.interact([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.interact([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.interact([('a', '4')])
    with pytest.raises(TypeError):
        m.interact([('a', LyingI())])
    with pytest.raises(TypeError):
        m.interact([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.interact([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.interact([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.interact([('ok', 4), ('ok', 3), (7, 4)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.interact([('ok', 4), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.interact({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.interact(ListSub([('a', 4)]))
    with pytest.raises(TypeError):
        m.interact([ListSub(('a', 4))])
    # tuple rows accepted exactly like lists
    assert m.interact((('a', 4),)) == m.interact([('a', 4)])
    # boundary acceptance pins
    assert m.interact([('abcdefgh', 4)])['total'] == 1
    assert m.interact([('a', 1)] * 100)['total'] == 100
    assert m.interact([('a', 0)])['uncrossed'] == ['a']
    assert m.interact([('a', 10)])['crossed'] == {'a': 1}
    # default-start pin: unknown robot must start at running 0
    assert m.interact([('zz', 4)])['uncrossed'] == ['zz']  # 0+4-2=2 < 3
    r = m.interact([('zz', 4), ('zz', 4)])
    assert r['crossed'] == {'zz': 2}  # 2, then 4; a default of 1 crosses at step 1
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
    ('running.get(robot, 0) + signal - DECAY', 'running.get(robot, 0) + signal'),
    ('running.get(robot, 0) + signal - DECAY', 'running.get(robot, 0) + signal - 1'),
    ('running.get(robot, 0) + signal - DECAY', 'running.get(robot, 0) + signal - DECAY + 1'),
    ('running.get(robot, 0)', 'running.get(robot, 1)'),
    ('DECAY = 2', 'DECAY = 3'),
    ('DECAY = 2', 'DECAY = 0'),
    ('CROSS = 3', 'CROSS = 4'),
    ('CROSS = 3', 'CROSS = 2'),
    ('if running[robot] >= CROSS and robot not in crossed:',
     'if running[robot] > CROSS and robot not in crossed:'),
    ('if running[robot] >= CROSS and robot not in crossed:',
     'if running[robot] >= CROSS:'),
    ('if running[robot] >= CROSS and robot not in crossed:',
     'if running[robot] >= CROSS and robot in crossed:'),
    ('crossed[robot] = index', 'crossed[robot] = index - 1'),
    ('crossed[robot] = index', 'crossed[robot] = index + 1'),
    ('robot for robot in running if robot not in crossed',
     'robot for robot in running if robot in crossed'),
    ("'total': len(rows)", "'total': len(crossed)"),
    ('robot, signal = row', 'signal, robot = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MIN_SIGNAL = 0', 'MIN_SIGNAL = 1'),
    ('MAX_SIGNAL = 10', 'MAX_SIGNAL = 9'),
    ('not MIN_SIGNAL <= signal <= MAX_SIGNAL', 'not MIN_SIGNAL < signal < MAX_SIGNAL'),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(robot) <= MAX_NAME', 'not 1 <= len(robot) < MAX_NAME'),
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
    assert 'Row 944, Epigenetic Robotics' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
