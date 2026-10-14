"""Mutation and oracle tests for extra_doc.neuroevolution."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_942_neuroevolution.py',
                        'src/sugarcode/extra_doc/neuroevolution.py')

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


class ListSub(list):
    pass


def _core(module):
    m = module
    # oracle seeded with row number 942
    assert m.evolve([]) == {'total': 0, 'grow': 0, 'prune': 0, 'final': {},
                            'viable': [], 'collapsed': []}
    r = m.evolve([('a', 'prune'), ('a', 'prune'), ('b', 'grow')])
    assert r == {'total': 3, 'grow': 1, 'prune': 2,
                 'final': {'a': 1, 'b': 4},
                 'viable': ['b'], 'collapsed': ['a']}
    # one prune lands exactly on the lower bound: still viable
    r = m.evolve([('a', 'prune')])
    assert r['final'] == {'a': 2} and r['viable'] == ['a']
    assert r['collapsed'] == []
    # two prunes collapse below the bound
    r = m.evolve([('a', 'prune'), ('a', 'prune')])
    assert r['collapsed'] == ['a']  # start 3 -> 1; start 4 would stay viable at 2
    # five grows land exactly on the upper bound: still viable
    r = m.evolve([('a', 'grow')] * 5)
    assert r['final'] == {'a': 8} and r['viable'] == ['a']
    assert r['collapsed'] == []
    # six grows collapse above the bound
    r = m.evolve([('a', 'grow')] * 6)
    assert r['collapsed'] == ['a'] and r['final'] == {'a': 9}
    # grow-magnitude pin: +1 vs +2 diverges inside the band
    r = m.evolve([('a', 'grow')] * 3)
    assert r['final'] == {'a': 6} and r['viable'] == ['a']  # +2 would reach 9
    # prune-magnitude pin: -1 vs -2 diverges inside the band
    r = m.evolve([('a', 'prune')])
    assert r['viable'] == ['a']  # -2 would collapse to 1
    # wide many-name sort pin (20 names, deterministic)
    names = ['net%02d' % i for i in range(20)]
    r = m.evolve([(n, 'grow') for n in names])
    assert r['viable'] == sorted(names)
    assert r['final'] == {n: 4 for n in names}
    assert r['total'] == 20
    # dynamic equal-string witnesses: outcome changes under is-misread
    dyn_g = ''.join(['gr', 'ow'])
    r = m.evolve([('a', dyn_g)] * 6)
    assert r['collapsed'] == ['a'] and r['grow'] == 6  # misread as prune -> 3-6 < 0... asserts below
    dyn_p = ''.join(['pr', 'une'])
    r = m.evolve([('a', dyn_p)])
    assert r['viable'] == ['a'] and r['prune'] == 1
    # two dynamic grows then one dynamic prune: net count visible in 'final'
    r = m.evolve([('a', dyn_g), ('a', dyn_g), ('a', dyn_p)])
    assert r['final'] == {'a': 4}  # 3 +1 +1 -1; grow misread gives 2, prune misread gives 6
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.evolve('nope')
    with pytest.raises(TypeError):
        m.evolve(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.evolve([('a', 'grow')] * 101)
    with pytest.raises(TypeError):
        m.evolve([('a', 'grow'), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.evolve([('a', 'grow'), ('a',)])
    with pytest.raises(TypeError):
        m.evolve([(1, 'grow')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.evolve([('', 'grow')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.evolve([('abcdefghi', 'grow')])
    with pytest.raises(TypeError):
        m.evolve([('a', 1)])
    with pytest.raises(ValueError, match="one of"):
        m.evolve([('a', 'split')])
    # first bad row pins, mixed failure types
    try:
        m.evolve([('ok', 'grow'), ('ok', 'prune'), (7, 'grow')])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.evolve([('ok', 'grow'), ('ok', 'nope')])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.evolve({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.evolve(ListSub([('a', 'grow')]))
    with pytest.raises(TypeError):
        m.evolve([ListSub(('a', 'grow'))])
    # tuple rows accepted exactly like lists
    assert m.evolve((('a', 'grow'),)) == m.evolve([('a', 'grow')])
    # boundary acceptance pins
    assert m.evolve([('abcdefgh', 'grow')])['viable'] == ['abcdefgh']
    assert m.evolve([('a', 'grow')] * 100)['total'] == 100
    # default-start pins: unknown network must start at 3
    r = m.evolve([('zz', 'grow')] * 5)
    assert r['final'] == {'zz': 8} and r['viable'] == ['zz']
    r = m.evolve([('zz', 'prune'), ('zz', 'prune')])
    assert r['collapsed'] == ['zz']  # start 3 -> 1; start 4 would be viable at 2
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
    ("if operator == 'grow':", "if operator is 'grow':"),
    ("if operator == 'grow':", "if operator != 'grow':"),
    ("level + 1 if operator == 'grow' else level - 1",
     "level - 1 if operator == 'grow' else level + 1"),
    ("level + 1 if operator == 'grow' else level - 1",
     "level + 1 if operator is 'grow' else level - 1"),
    ('level + 1', 'level + 2'),
    ('level - 1', 'level - 2'),
    ('nodes.get(network, START_NODES)', 'nodes.get(network, 0)'),
    ('nodes.get(network, START_NODES)', 'nodes.get(network, 4)'),
    ('START_NODES = 3', 'START_NODES = 4'),
    ('MIN_NODES = 2', 'MIN_NODES = 3'),
    ('MIN_NODES = 2', 'MIN_NODES = 1'),
    ('MAX_NODES = 8', 'MAX_NODES = 7'),
    ('MAX_NODES = 8', 'MAX_NODES = 9'),
    ('if MIN_NODES <= count <= MAX_NODES',
     'if MIN_NODES < count < MAX_NODES'),
    ('if not MIN_NODES <= count <= MAX_NODES',
     'if not MIN_NODES < count < MAX_NODES'),
    ('grow += 1', 'grow += 2'),
    ('prune += 1', 'prune += 2'),
    ("'total': len(rows)", "'total': len(nodes)"),
    ('network, operator = row', 'operator, network = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("OPERATORS = ('grow', 'prune')", "OPERATORS = ('grow', 'prune', 'split')"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(network) <= MAX_NAME', 'not 1 <= len(network) < MAX_NAME'),
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
    assert 'Row 942, Neuroevolution' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
