"""Mutation and oracle tests for extra_doc.metamaterials."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_953_metamaterials.py',
                        'src/sugarcode/extra_doc/metamaterials.py')

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
        return 2


class ListSub(list):
    pass


def _core(module):
    m = module
    # oracle seeded with row number 953
    assert m.tune([]) == {'total': 0, 'cells': 0, 'ratios': {},
                          'tuned': []}
    # aggregation before reduction: 1:3 + 2:3 -> 3:6 -> [1, 2]
    r = m.tune([('a', 1, 3), ('a', 2, 3)])
    assert r == {'total': 2, 'cells': 1, 'ratios': {'a': [1, 2]},
                 'tuned': ['a']}
    # a single record already on ratio
    r = m.tune([('a', 2, 4)])
    assert r['ratios'] == {'a': [1, 2]} and r['tuned'] == ['a']
    # equal dimensions reduce to [1, 1]
    r = m.tune([('a', 5, 5)])
    assert r['ratios'] == {'a': [1, 1]} and r['tuned'] == []
    # gcd exactness: 6:9 reduces by 3, not left alone
    r = m.tune([('a', 6, 9)])
    assert r['ratios'] == {'a': [2, 3]}
    # coprime pair stays
    r = m.tune([('a', 3, 4)])
    assert r['ratios'] == {'a': [3, 4]} and r['tuned'] == []
    # the target is 1:2, not 2:1
    r = m.tune([('a', 4, 2)])
    assert r['ratios'] == {'a': [2, 1]} and r['tuned'] == []
    # several cells: only on-ratio ones tune
    r = m.tune([('b', 1, 2), ('a', 3, 6), ('c', 2, 2)])
    assert r['tuned'] == ['a', 'b'] and r['cells'] == 3
    # dynamic equal-string witness: equal cells aggregate together
    dyn = ''.join(['c', '1'])
    r = m.tune([(dyn, 1, 3), (''.join(['c', '1']), 2, 3)])
    assert r['ratios'] == {'c1': [1, 2]} and r['tuned'] == ['c1']
    # wide many-name sort pin (20 cells on ratio)
    names = ['uc%02d' % i for i in range(20)]
    r = m.tune([(n, 1, 2) for n in names])
    assert r['tuned'] == sorted(names)
    assert r['ratios'] == {n: [1, 2] for n in names} and r['cells'] == 20
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.tune('nope')
    with pytest.raises(TypeError):
        m.tune(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.tune([('a', 1, 2)] * 101)
    with pytest.raises(TypeError):
        m.tune([('a', 1, 2), 'bad'])
    with pytest.raises(ValueError, match='3 fields'):
        m.tune([('a', 1, 2), ('a', 1)])
    with pytest.raises(TypeError):
        m.tune([(1, 1, 2)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.tune([('', 1, 2)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.tune([('abcdefghi', 1, 2)])
    with pytest.raises(TypeError):
        m.tune([('a', '1', 2)])
    with pytest.raises(TypeError):
        m.tune([('a', 1, '2')])
    with pytest.raises(TypeError):
        m.tune([('a', LyingI(), 2)])
    with pytest.raises(TypeError):
        m.tune([('a', True, 2)])
    with pytest.raises(ValueError, match='1-10'):
        m.tune([('a', 0, 2)])
    with pytest.raises(ValueError, match='1-10'):
        m.tune([('a', 1, 11)])
    # first bad row pins, mixed failure types
    try:
        m.tune([('ok', 1, 2), ('ok', 1, 2), (7, 1, 2)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.tune([('ok', 1, 2), ('ok', 99, 2)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.tune({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.tune(ListSub([('a', 1, 2)]))
    with pytest.raises(TypeError):
        m.tune([ListSub(('a', 1, 2))])
    # tuple rows accepted exactly like lists
    assert m.tune((('a', 1, 2),)) == m.tune([('a', 1, 2)])
    # boundary acceptance pins
    assert m.tune([('abcdefgh', 1, 2)])['tuned'] == ['abcdefgh']
    assert m.tune([('a', 1, 2)] * 100)['total'] == 100
    assert m.tune([('a', 1, 1)])['ratios'] == {'a': [1, 1]}
    assert m.tune([('a', 10, 10)])['ratios'] == {'a': [1, 1]}
    assert m.tune([('a', 5, 10)])['tuned'] == ['a']
    # default-start pins: unknown cell must start both sums at 0
    r = m.tune([('zz', 3, 6)])
    assert r['ratios'] == {'zz': [1, 2]} and r['tuned'] == ['zz']
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
    ('TARGET = (1, 2)', 'TARGET = (1, 3)'),
    ('TARGET = (1, 2)', 'TARGET = (2, 1)'),
    ('reduced == [TARGET[0], TARGET[1]]', 'reduced == [TARGET[1], TARGET[0]]'),
    ('pitch // factor', 'pitch // factor + 1'),
    ('width // factor', 'width // factor + 1'),
    ('a, b = b, a % b', 'a, b = b, a // b'),
    ('pitches.get(cell, 0) + pitch', 'pitches.get(cell, 0) - pitch'),
    ('pitches.get(cell, 0)', 'pitches.get(cell, 1)'),
    ('widths.get(cell, 0)', 'widths.get(cell, 1)'),
    ("'cells': len(pitches)", "'cells': len(rows)"),
    ("'total': len(rows)", "'total': len(pitches)"),
    ('cell, pitch, width = row', 'cell, width, pitch = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MIN_DIM = 1', 'MIN_DIM = 0'),
    ('MIN_DIM = 1', 'MIN_DIM = 2'),
    ('MAX_DIM = 10', 'MAX_DIM = 9'),
    ('not MIN_DIM <= value <= MAX_DIM', 'not MIN_DIM < value < MAX_DIM'),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(cell) <= MAX_NAME', 'not 1 <= len(cell) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 3', 'len(row) != 2'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 953, Metamaterials' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True


class S(str):
    pass


def _exact(fn, exc_type, expected):
    with pytest.raises(exc_type) as info:
        fn()
    assert str(info.value) == expected


def test_str_subclass_rejected_v2():
    m = _load_code(SRC)
    _exact(lambda: m.tune([(S('a'), 2, 4)]), TypeError,
           'row 1: cell must be str, got S')


def test_error_messages_exact_v2():
    m = _load_code(SRC)
    _exact(lambda: m.tune('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.tune(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.tune({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.tune([('a', 2, 4)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.tune([('a', 2, 4), 'bad']), TypeError,
           'row 2: expected (cell, pitch, width) tuple, got str')
    _exact(lambda: m.tune([('a', 2, 4), ('a', 2)]), ValueError,
           'row 2: expected 3 fields, got 2')
    _exact(lambda: m.tune([(1, 2, 4)]), TypeError,
           'row 1: cell must be str, got int')
    _exact(lambda: m.tune([(True, 2, 4)]), TypeError,
           'row 1: cell must be str, got bool')
    _exact(lambda: m.tune([('', 2, 4)]), ValueError,
           'row 1: cell must be 1-8 chars')
    _exact(lambda: m.tune([('abcdefghi', 2, 4)]), ValueError,
           'row 1: cell must be 1-8 chars')
    _exact(lambda: m.tune([('a', '2', 4)]), TypeError,
           'row 1: pitch must be int, got str')
    _exact(lambda: m.tune([('a', 2, '4')]), TypeError,
           'row 1: width must be int, got str')
    _exact(lambda: m.tune([('a', True, 4)]), TypeError,
           'row 1: pitch must be int, got bool')
    _exact(lambda: m.tune([('a', 0, 4)]), ValueError,
           'row 1: pitch must be 1-10, got 0')
    _exact(lambda: m.tune([('a', 11, 4)]), ValueError,
           'row 1: pitch must be 1-10, got 11')
    _exact(lambda: m.tune([('a', 2, 0)]), ValueError,
           'row 1: width must be 1-10, got 0')
    _exact(lambda: m.tune([('a', 2, 11)]), ValueError,
           'row 1: width must be 1-10, got 11')
    _exact(lambda: m.tune([('a', 2, 4), ('a', 2, 4), (1, 2, 4)]),
           TypeError, 'row 3: cell must be str, got int')


def test_scope_wording_exact_v2():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: geometric ratio tuning only; no EM simulation'
    assert module.NOT_CLAIMED == (
        'does not simulate electromagnetic response',
        'does not model frequency dependence',
        'does not optimize the geometry',
        'does not handle more than two structural dimensions',
    )
