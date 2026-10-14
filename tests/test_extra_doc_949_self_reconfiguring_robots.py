"""Mutation and oracle tests for extra_doc.self_reconfiguring_robots."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_949_self_reconfiguring_robots.py',
                        'src/sugarcode/extra_doc/self_reconfiguring_robots.py')

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
    # oracle seeded with row number 949
    assert m.reconfigure([]) == {'total': 0, 'shapes': {},
                                 'symmetric': [], 'longest': 0}
    # 1,2,1 reads the same from both ends
    r = m.reconfigure([('a', 1), ('a', 2), ('a', 1)])
    assert r == {'total': 3, 'shapes': {'a': 3}, 'symmetric': ['a'],
                 'longest': 3}
    # equal pair settles
    r = m.reconfigure([('a', 1), ('a', 1)])
    assert r['symmetric'] == ['a'] and r['longest'] == 2
    # differing pair does not (kills any always-symmetric comparison)
    r = m.reconfigure([('a', 1), ('a', 2)])
    assert r['symmetric'] == [] and r['shapes'] == {'a': 2}
    # a single segment is not yet a shape
    r = m.reconfigure([('a', 3)])
    assert r['symmetric'] == [] and r['shapes'] == {'a': 1}
    # off-center palindrome still settles; asymmetric four does not
    r = m.reconfigure([('a', 4), ('a', 0), ('a', 4)])
    assert r['symmetric'] == ['a']
    r = m.reconfigure([('a', 1), ('a', 1), ('a', 2), ('a', 2)])
    assert r['symmetric'] == []
    # longest tracks the biggest shape across robots
    r = m.reconfigure([('a', 1), ('a', 1), ('b', 1), ('b', 2), ('b', 1)])
    assert r['longest'] == 3 and r['shapes'] == {'a': 2, 'b': 3}
    assert r['symmetric'] == ['a', 'b']
    # dynamic equal-string witness: equal robots share one shape
    dyn = ''.join(['r', '1'])
    r = m.reconfigure([(dyn, 1), (''.join(['r', '1']), 1)])
    assert r['shapes'] == {'r1': 2} and r['symmetric'] == ['r1']
    # wide many-name sort pin (20 robots, deterministic)
    names = ['rb%02d' % i for i in range(20)]
    rows = [(n, 1) for n in names] + [(n, 1) for n in names]
    r = m.reconfigure(rows)
    assert r['symmetric'] == sorted(names)
    assert r['shapes'] == {n: 2 for n in names} and r['longest'] == 2
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.reconfigure('nope')
    with pytest.raises(TypeError):
        m.reconfigure(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.reconfigure([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.reconfigure([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.reconfigure([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.reconfigure([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.reconfigure([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.reconfigure([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.reconfigure([('a', '1')])
    with pytest.raises(TypeError):
        m.reconfigure([('a', LyingI())])
    with pytest.raises(TypeError):
        m.reconfigure([('a', True)])
    with pytest.raises(ValueError, match='0-9'):
        m.reconfigure([('a', 10)])
    with pytest.raises(ValueError, match='0-9'):
        m.reconfigure([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.reconfigure([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.reconfigure([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.reconfigure({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.reconfigure(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.reconfigure([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.reconfigure((('a', 1),)) == m.reconfigure([('a', 1)])
    # boundary acceptance pins
    assert m.reconfigure([('abcdefgh', 1), ('abcdefgh', 1)])['symmetric'] == ['abcdefgh']
    assert m.reconfigure([('a', 1)] * 100)['total'] == 100
    assert m.reconfigure([('a', 0), ('a', 0)])['symmetric'] == ['a']
    assert m.reconfigure([('a', 9), ('a', 9)])['symmetric'] == ['a']
    # default-start pin: unknown robot must start with an empty shape
    r = m.reconfigure([('zz', 4), ('zz', 4)])
    assert r['shapes'] == {'zz': 2} and r['symmetric'] == ['zz']
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
    ('shape == shape[::-1]', 'shape == shape'),
    ('shape == shape[::-1]', 'shape != shape[::-1]'),
    ('shape == shape[::-1]', 'sorted(shape) == sorted(shape[::-1])'),
    ('shape[::-1]', 'shape[::1]'),
    ('len(shape) >= MIN_SHAPE', 'len(shape) > MIN_SHAPE'),
    ('len(shape) >= MIN_SHAPE', 'len(shape) >= MIN_SHAPE + 1'),
    ('MIN_SHAPE = 2', 'MIN_SHAPE = 1'),
    ('max((len(shape) for shape in shapes.values()), default=0)',
     'min((len(shape) for shape in shapes.values()), default=0)'),
    ('max((len(shape) for shape in shapes.values()), default=0)',
     'max((len(shape) for shape in shapes.values()))'),
    ("'total': len(rows)", "'total': len(shapes)"),
    ('robot, segment = row', 'segment, robot = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MIN_SEGMENT = 0', 'MIN_SEGMENT = 1'),
    ('MAX_SEGMENT = 9', 'MAX_SEGMENT = 8'),
    ('not MIN_SEGMENT <= segment <= MAX_SEGMENT',
     'not MIN_SEGMENT < segment < MAX_SEGMENT'),
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
    assert 'Row 949, Self-Reconfiguring Robots' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
