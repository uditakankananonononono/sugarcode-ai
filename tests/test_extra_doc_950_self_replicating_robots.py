"""Mutation and oracle tests for extra_doc.self_replicating_robots."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_950_self_replicating_robots.py',
                        'src/sugarcode/extra_doc/self_replicating_robots.py')

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
        return 1


class ListSub(list):
    pass


def _core(module):
    m = module
    # oracle seeded with row number 950
    assert m.replicate([]) == {'total': 0, 'mutations': {},
                               'stable': [], 'drifted': []}
    # every consecutive pair counts: 1,2,1 drifts twice despite equal ends
    r = m.replicate([('a', 1), ('a', 2), ('a', 1)])
    assert r == {'total': 3, 'mutations': {'a': 2}, 'stable': [],
                 'drifted': ['a']}
    # monotone drift counts each step
    r = m.replicate([('a', 1), ('a', 2), ('a', 3)])
    assert r['mutations'] == {'a': 2}
    # equal consecutive codes are not mutations
    r = m.replicate([('a', 1), ('a', 1), ('a', 2)])
    assert r['mutations'] == {'a': 1}
    # unchanged lineage with enough records is stable
    r = m.replicate([('a', 5), ('a', 5)])
    assert r == {'total': 2, 'mutations': {}, 'stable': ['a'],
                 'drifted': []}
    r = m.replicate([('a', 5), ('a', 5), ('a', 5), ('a', 5)])
    assert r['stable'] == ['a']
    # a single record is neither stable nor drifted
    r = m.replicate([('a', 5)])
    assert r == {'total': 1, 'mutations': {}, 'stable': [], 'drifted': []}
    # robots are independent lineages
    r = m.replicate([('a', 1), ('b', 7), ('a', 1), ('b', 8)])
    assert r['mutations'] == {'b': 1} and r['stable'] == ['a']
    assert r['drifted'] == ['b']
    # dynamic equal-string witness: equal robots share one lineage
    dyn = ''.join(['r', '1'])
    r = m.replicate([(dyn, 1), (''.join(['r', '1']), 2)])
    assert r['mutations'] == {'r1': 1} and r['drifted'] == ['r1']
    # wide many-name sort pin (20 robots, deterministic)
    names = ['rp%02d' % i for i in range(20)]
    rows = [(n, 1) for n in names] + [(n, 1) for n in names]
    r = m.replicate(rows)
    assert r['stable'] == sorted(names)
    assert r['mutations'] == {} and r['drifted'] == []
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.replicate('nope')
    with pytest.raises(TypeError):
        m.replicate(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.replicate([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.replicate([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.replicate([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.replicate([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.replicate([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.replicate([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.replicate([('a', '1')])
    with pytest.raises(TypeError):
        m.replicate([('a', LyingI())])
    with pytest.raises(TypeError):
        m.replicate([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.replicate([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.replicate([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.replicate([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.replicate([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.replicate({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.replicate(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.replicate([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.replicate((('a', 1),)) == m.replicate([('a', 1)])
    # boundary acceptance pins
    assert m.replicate([('abcdefgh', 1), ('abcdefgh', 1)])['stable'] == ['abcdefgh']
    assert m.replicate([('a', 1)] * 100)['total'] == 100
    assert m.replicate([('a', 0), ('a', 0)])['stable'] == ['a']
    assert m.replicate([('a', 10), ('a', 10)])['stable'] == ['a']
    # default-start pin: unknown robot must start with no history
    r = m.replicate([('zz', 4), ('zz', 4)])
    assert r['stable'] == ['zz'] and r['mutations'] == {}
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
    ('code != last[robot]', 'code == last[robot]'),
    ('if robot in last and code != last[robot]:',
     'if code != last.get(robot):'),
    ('last[robot] = code', 'last[robot] = last.get(robot, code)'),
    ('changes.get(robot, 0) + 1', 'changes.get(robot, 0) + 2'),
    ('changes.get(robot, 0)', 'changes.get(robot, 1)'),
    ('counts.get(robot, 0) + 1', 'counts.get(robot, 0) + 2'),
    ('count >= MIN_RECORDS', 'count > MIN_RECORDS'),
    ('count >= MIN_RECORDS', 'count >= MIN_RECORDS + 1'),
    ('MIN_RECORDS = 2', 'MIN_RECORDS = 1'),
    ('robot not in changes', 'robot in changes'),
    ('drifted = sorted(changes)', 'drifted = sorted(counts)'),
    ("'total': len(rows)", "'total': len(last)"),
    ("'mutations': dict(changes)", "'mutations': dict(counts)"),
    ('robot, code = row', 'code, robot = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MIN_CODE = 0', 'MIN_CODE = 1'),
    ('MAX_CODE = 10', 'MAX_CODE = 9'),
    ('not MIN_CODE <= code <= MAX_CODE', 'not MIN_CODE < code < MAX_CODE'),
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
    assert 'Row 950, Self-Replicating Robots' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
