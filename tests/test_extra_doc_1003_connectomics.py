"""Mutation and oracle tests for extra_doc.connectomics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_1003_connectomics.py',
                        'src/sugarcode/extra_doc/connectomics.py')

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


class S(str):
    pass


def _exact(fn, exc_type, expected):
    with pytest.raises(exc_type) as info:
        fn()
    assert str(info.value) == expected


def _core(module):
    m = module
    # oracle seeded with row number 1003
    assert m.map([]) == {'total': 0, 'cores': {}, 'units': []}
    # strengths 2, 4 reduce to 2
    r = m.map([('w', 2), ('w', 4)])
    assert r == {'total': 2, 'cores': {'w': 2}, 'units': []}
    # 3, 5 reduce to 1 and read as a unit
    r = m.map([('w', 3), ('w', 5)])
    assert r == {'total': 2, 'cores': {'w': 1}, 'units': ['w']}
    # 4, 6 reduce to 2
    r = m.map([('w', 4), ('w', 6)])
    assert r == {'total': 2, 'cores': {'w': 2}, 'units': []}
    # 0, 5 reduce to 5
    r = m.map([('w', 0), ('w', 5)])
    assert r == {'total': 2, 'cores': {'w': 5}, 'units': []}
    # 0, 0 reduce to 0
    r = m.map([('w', 0), ('w', 0)])
    assert r == {'total': 2, 'cores': {'w': 0}, 'units': []}
    # a lone strength reduces to itself
    r = m.map([('w', 7)])
    assert r == {'total': 1, 'cores': {'w': 7}, 'units': []}
    # 6, 9, 3 reduce to 3
    r = m.map([('w', 6), ('w', 9), ('w', 3)])
    assert r == {'total': 3, 'cores': {'w': 3}, 'units': []}
    # 6, 10, 3 reduce to 1 and read as a unit
    r = m.map([('w', 6), ('w', 10), ('w', 3)])
    assert r == {'total': 3, 'cores': {'w': 1}, 'units': ['w']}
    # boundary strengths: 10, 10 reduce to 10; 10, 5 reduce to 5
    r = m.map([('w', 10), ('w', 10)])
    assert r['cores'] == {'w': 10}
    r = m.map([('w', 10), ('w', 5)])
    assert r['cores'] == {'w': 5}
    # 9, 6 reduce to 3; 9, 2 reduce to 1 and read as a unit
    r = m.map([('w', 9), ('w', 6)])
    assert r['cores'] == {'w': 3}
    r = m.map([('w', 9), ('w', 2)])
    assert r['cores'] == {'w': 1} and r['units'] == ['w']
    # each node keeps its own divisor
    r = m.map([('a', 2), ('b', 3), ('a', 4), ('b', 5)])
    assert r == {'total': 4, 'cores': {'a': 2, 'b': 1},
                 'units': ['b']}
    # dynamic equal-string witness: equal nodes share one divisor
    dyn = ''.join(['w', '1'])
    r = m.map([(dyn, 2), (''.join(['w', '1']), 4)])
    assert r['cores'] == {'w1': 2} and r['units'] == []
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['n%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 3), (n, 5)]
    r = m.map(rows)
    assert r['units'] == sorted(names)
    assert r['cores'] == {n: 1 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.map('nope')
    with pytest.raises(TypeError):
        m.map(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.map([('w', 1)] * 101)
    with pytest.raises(TypeError):
        m.map([('w', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.map([('w', 1), ('w',)])
    with pytest.raises(TypeError):
        m.map([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.map([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.map([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.map([('w', '1')])
    with pytest.raises(TypeError):
        m.map([('w', LyingI())])
    with pytest.raises(TypeError):
        m.map([('w', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.map([('w', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.map([('w', -1)])
    # first bad row pins, mixed failure types
    try:
        m.map([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.map([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.map({'w': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.map(ListSub([('w', 1)]))
    with pytest.raises(TypeError):
        m.map([ListSub(('w', 1))])
    # tuple rows accepted exactly like lists
    assert m.map((('w', 1),)) == m.map([('w', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.map([('w', 2), ['w', 4], ('w', 4)])
    assert mixed == m.map([['w', 2], ('w', 4), ['w', 4]])
    # boundary acceptance pins
    assert m.map([('abcdefgh', 1)])['cores'] == {'abcdefgh': 1}
    assert m.map([('w', 1)] * 100)['total'] == 100
    assert m.map([('w', 0)])['cores'] == {'w': 0}
    assert m.map([('w', 10)])['cores'] == {'w': 10}
    # default-start pins: unknown node starts with no divisor
    r = m.map([('zz', 4), ('zz', 4)])
    assert r['cores'] == {'zz': 4} and r['units'] == []
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
    ('core = math.gcd(core, strength)', 'core = strength'),
    ('core = math.gcd(core, strength)', 'core = math.gcd(core, 1)'),
    ('core = 0', 'core = 1'),
    ('for strength in vals:', 'for strength in vals[1:]:'),
    ('core == 1', 'core != 1'),
    ('core == 1', 'core == 0'),
    ('units = sorted(', 'units = list('),
    ('units = sorted(node for node, core in cores.items() if core == 1)',
     'units = sorted((node for node, core in cores.items() if core == 1), reverse=True)'),
    ('values.setdefault(node, []).append(strength)',
     'values.setdefault(node, [3]).append(strength)'),
    ('values: dict = {}', "values: dict = {'zz': [2, 4]}"),
    ('cores = {}', "cores = {'zz': 5}"),
    ('node, strength = row', 'strength, node = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(cores)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(node) <= MAX_NAME',
     'not 1 <= len(node) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_STRENGTH = 0', 'MIN_STRENGTH = 1'),
    ('MAX_STRENGTH = 10', 'MAX_STRENGTH = 9'),
    ('not MIN_STRENGTH <= strength <= MAX_STRENGTH',
     'not MIN_STRENGTH < strength < MAX_STRENGTH'),
    ("'cores': cores", "'cores': units"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.map([(S('w'), 5)]), TypeError,
           'row 1: node must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.map('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.map(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.map({'w': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.map([('w', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.map([('w', 1), 'bad']), TypeError,
           'row 2: expected (node, strength) tuple, got str')
    _exact(lambda: m.map([('w', 1), ('w',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.map([(1, 1)]), TypeError,
           'row 1: node must be str, got int')
    _exact(lambda: m.map([(True, 1)]), TypeError,
           'row 1: node must be str, got bool')
    _exact(lambda: m.map([('', 1)]), ValueError,
           'row 1: node must be 1-8 chars')
    _exact(lambda: m.map([('abcdefghi', 1)]), ValueError,
           'row 1: node must be 1-8 chars')
    _exact(lambda: m.map([('w', '1')]), TypeError,
           'row 1: strength must be int, got str')
    _exact(lambda: m.map([('w', True)]), TypeError,
           'row 1: strength must be int, got bool')
    _exact(lambda: m.map([('w', 11)]), ValueError,
           'row 1: strength must be 0-10, got 11')
    _exact(lambda: m.map([('w', -1)]), ValueError,
           'row 1: strength must be 0-10, got -1')
    _exact(lambda: m.map([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: node must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 1003, Connectomics' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: connection bookkeeping only; no graph topology modeled'
    assert module.NOT_CLAIMED == (
        'does not model direction of connections',
        'does not weight strengths by record order',
        'does not measure distance between nodes',
        'does not compare nodes against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
