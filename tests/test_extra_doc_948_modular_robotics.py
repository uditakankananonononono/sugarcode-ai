"""Mutation and oracle tests for extra_doc.modular_robotics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_948_modular_robotics.py',
                        'src/sugarcode/extra_doc/modular_robotics.py')

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
    # oracle seeded with row number 948
    assert m.dock([]) == {'total': 0, 'modules': 0, 'structures': 0,
                          'largest': 0, 'singletons': []}
    # two separate pairs
    r = m.dock([('a', 'b'), ('c', 'd')])
    assert r == {'total': 2, 'modules': 4, 'structures': 2, 'largest': 2,
                 'singletons': []}
    # chaining merges through the shared module
    r = m.dock([('a', 'b'), ('b', 'c')])
    assert r == {'total': 2, 'modules': 3, 'structures': 1, 'largest': 3,
                 'singletons': []}
    # a late bridge joins two clusters into one
    r = m.dock([('a', 'b'), ('c', 'd'), ('b', 'c')])
    assert r['structures'] == 1 and r['largest'] == 4 and r['modules'] == 4
    # a self-dock leaves a singleton structure
    r = m.dock([('a', 'a')])
    assert r == {'total': 1, 'modules': 1, 'structures': 1, 'largest': 1,
                 'singletons': ['a']}
    # self-dock then real dock: no longer a singleton
    r = m.dock([('a', 'a'), ('a', 'b')])
    assert r['singletons'] == [] and r['structures'] == 1
    # mixed sizes: largest picks the biggest structure
    r = m.dock([('a', 'b'), ('c', 'd'), ('d', 'e')])
    assert r['structures'] == 2 and r['largest'] == 3
    # dynamic equal-string witness: equal modules merge into one cluster
    dyn = ''.join(['m', '1'])
    r = m.dock([(dyn, 'b'), (''.join(['m', '1']), 'c')])
    assert r['structures'] == 1 and r['largest'] == 3 and r['modules'] == 3
    # wide many-name sort pin (20 singletons, deterministic)
    names = ['mod%02d' % i for i in range(20)]
    r = m.dock([(n, n) for n in names])
    assert r['singletons'] == sorted(names)
    assert r['structures'] == 20 and r['largest'] == 1 and r['modules'] == 20
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.dock('nope')
    with pytest.raises(TypeError):
        m.dock(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.dock([('a', 'b')] * 101)
    with pytest.raises(TypeError):
        m.dock([('a', 'b'), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.dock([('a', 'b'), ('a',)])
    with pytest.raises(TypeError):
        m.dock([(1, 'b')])
    with pytest.raises(TypeError):
        m.dock([('a', 1)])
    with pytest.raises(TypeError):
        m.dock([(LyingS(), 'b')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.dock([('', 'b')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.dock([('abcdefghi', 'b')])
    # first bad row pins, mixed failure types
    try:
        m.dock([('ok', 'b'), ('ok', 'c'), (7, 'b')])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.dock([('ok', 'b'), ('ok', '')])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.dock({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.dock(ListSub([('a', 'b')]))
    with pytest.raises(TypeError):
        m.dock([ListSub(('a', 'b'))])
    # tuple rows accepted exactly like lists
    assert m.dock((('a', 'b'),)) == m.dock([('a', 'b')])
    # boundary acceptance pins
    assert m.dock([('abcdefgh', 'b')])['modules'] == 2
    assert m.dock([('a', 'b')] * 100)['total'] == 100
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
    ('if root_m != root_p:', 'if root_m == root_p:'),
    ('parent[root_p] = root_m', 'parent[root_p] = root_p'),
    ('sizes.get(root, 0) + 1', 'sizes.get(root, 0) + 2'),
    ('sizes.get(root, 0)', 'sizes.get(root, 1)'),
    ('max(sizes.values())', 'min(sizes.values())'),
    ('max(sizes.values()) if sizes else 0', 'max(sizes.values())'),
    ('len(sizes)', 'len(parent)'),
    ("'modules': len(parent)", "'modules': len(rows)"),
    ("'total': len(rows)", "'total': len(parent)"),
    ('parent[module] == module', 'parent[module] != module'),
    ('sizes.get(module, 0) == 1', 'sizes.get(module, 0) == 2'),
    ('sizes.get(module, 0) == 1', 'sizes.get(module, 0) != 1'),
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
    assert 'Row 948, Modular Robotics' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
