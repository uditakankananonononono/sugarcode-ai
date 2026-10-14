"""Mutation and oracle tests for extra_doc.immunotherapy."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_984_immunotherapy.py',
                        'src/sugarcode/extra_doc/immunotherapy.py')

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
    # oracle seeded with row number 984
    assert m.engage([]) == {'total': 0, 'elevated': {}, 'primed': []}
    # markers 2, 4, 6 average 4 and one record beats it
    r = m.engage([('c', 2), ('c', 4), ('c', 6)])
    assert r == {'total': 3, 'elevated': {'c': 1}, 'primed': []}
    # 4, 4, 4 average 4 and none beats it because beating is strict
    r = m.engage([('c', 4), ('c', 4), ('c', 4)])
    assert r == {'total': 3, 'elevated': {'c': 0}, 'primed': []}
    # 1, 4, 4 average 3 and two beat it, priming the cell
    r = m.engage([('c', 1), ('c', 4), ('c', 4)])
    assert r == {'total': 3, 'elevated': {'c': 2}, 'primed': ['c']}
    # 1, 2 average 1, the fractional part dropped, and one beats it
    r = m.engage([('c', 1), ('c', 2)])
    assert r == {'total': 2, 'elevated': {'c': 1}, 'primed': []}
    # a lone marker averages itself and never beats
    r = m.engage([('c', 5)])
    assert r == {'total': 1, 'elevated': {'c': 0}, 'primed': []}
    # three beats are primed too
    r = m.engage([('c', 1), ('c', 4), ('c', 4), ('c', 4)])
    assert r['elevated'] == {'c': 3} and r['primed'] == ['c']
    # the low records pull the average down: 1, 1, 3 averages 1
    r = m.engage([('c', 1), ('c', 1), ('c', 3)])
    assert r['elevated'] == {'c': 1}
    # each cell keeps its own average
    r = m.engage([('a', 1), ('b', 4), ('a', 4), ('b', 4), ('a', 4)])
    assert r == {'total': 5, 'elevated': {'a': 2, 'b': 0},
                 'primed': ['a']}
    # boundary markers
    r = m.engage([('c', 0), ('c', 10), ('c', 10)])
    assert r['elevated'] == {'c': 2} and r['primed'] == ['c']
    # dynamic equal-string witness: equal cells share one average
    dyn = ''.join(['c', '1'])
    r = m.engage([(dyn, 1), (''.join(['c', '1']), 4),
                  (''.join(['c', '1']), 4)])
    assert r['elevated'] == {'c1': 2} and r['primed'] == ['c1']
    # wide many-name sort pin, inserted in reverse order (20 cells)
    names = ['c%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 4), (n, 4)]
    r = m.engage(rows)
    assert r['primed'] == sorted(names)
    assert r['elevated'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.engage('nope')
    with pytest.raises(TypeError):
        m.engage(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.engage([('c', 1)] * 101)
    with pytest.raises(TypeError):
        m.engage([('c', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.engage([('c', 1), ('c',)])
    with pytest.raises(TypeError):
        m.engage([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.engage([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.engage([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.engage([('c', '1')])
    with pytest.raises(TypeError):
        m.engage([('c', LyingI())])
    with pytest.raises(TypeError):
        m.engage([('c', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.engage([('c', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.engage([('c', -1)])
    # first bad row pins, mixed failure types
    try:
        m.engage([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.engage([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.engage({'c': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.engage(ListSub([('c', 1)]))
    with pytest.raises(TypeError):
        m.engage([ListSub(('c', 1))])
    # tuple rows accepted exactly like lists
    assert m.engage((('c', 1),)) == m.engage([('c', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.engage([('c', 1), ['c', 4], ('c', 4)])
    assert mixed == m.engage([['c', 1], ('c', 4), ['c', 4]])
    # boundary acceptance pins
    assert m.engage([('abcdefgh', 1)])['elevated'] == {'abcdefgh': 0}
    assert m.engage([('c', 1)] * 100)['total'] == 100
    assert m.engage([('c', 0)])['elevated'] == {'c': 0}
    assert m.engage([('c', 10)])['elevated'] == {'c': 0}
    # default-start pins: unknown cell starts from an empty record
    r = m.engage([('zz', 1), ('zz', 4), ('zz', 4)])
    assert r['elevated'] == {'zz': 2} and r['primed'] == ['zz']
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
    ('average = sum(markers) // len(markers)',
     'average = sum(markers)'),
    ('average = sum(markers) // len(markers)',
     'average = sum(markers) // (len(markers) + 1)'),
    ('sum(1 for marker in markers if marker > average)',
     'sum(1 for marker in markers if marker >= average)'),
    ('sum(1 for marker in markers if marker > average)',
     'len(markers)'),
    ('sum(1 for marker in markers if marker > average)',
     'sum(2 for marker in markers if marker > average)'),
    ('values[cell] = []', 'values[cell] = [1]'),
    ('if cell not in values:', 'if cell in values:'),
    ('beats >= PRIMED', 'beats > PRIMED'),
    ('PRIMED = 2', 'PRIMED = 1'),
    ('PRIMED = 2', 'PRIMED = 3'),
    ('primed = sorted(', 'primed = list('),
    ('MIN_MARKER = 0', 'MIN_MARKER = 1'),
    ('MAX_MARKER = 10', 'MAX_MARKER = 9'),
    ('not MIN_MARKER <= marker <= MAX_MARKER',
     'not MIN_MARKER < marker < MAX_MARKER'),
    ('cell, marker = row', 'marker, cell = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(elevated)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(cell) <= MAX_NAME', 'not 1 <= len(cell) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'elevated': elevated", "'elevated': values"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.engage([(S('c'), 5)]), TypeError,
           'row 1: cell must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.engage('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.engage(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.engage({'c': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.engage([('c', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.engage([('c', 1), 'bad']), TypeError,
           'row 2: expected (cell, marker) tuple, got str')
    _exact(lambda: m.engage([('c', 1), ('c',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.engage([(1, 1)]), TypeError,
           'row 1: cell must be str, got int')
    _exact(lambda: m.engage([(True, 1)]), TypeError,
           'row 1: cell must be str, got bool')
    _exact(lambda: m.engage([('', 1)]), ValueError,
           'row 1: cell must be 1-8 chars')
    _exact(lambda: m.engage([('abcdefghi', 1)]), ValueError,
           'row 1: cell must be 1-8 chars')
    _exact(lambda: m.engage([('c', '1')]), TypeError,
           'row 1: marker must be int, got str')
    _exact(lambda: m.engage([('c', True)]), TypeError,
           'row 1: marker must be int, got bool')
    _exact(lambda: m.engage([('c', 11)]), ValueError,
           'row 1: marker must be 0-10, got 11')
    _exact(lambda: m.engage([('c', -1)]), ValueError,
           'row 1: marker must be 0-10, got -1')
    _exact(lambda: m.engage([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: cell must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 984, Immunotherapy' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: marker bookkeeping only; no immune response modeled'
    assert module.NOT_CLAIMED == (
        'does not model T-cell activation',
        'does not weight markers by record order',
        'does not round the average to nearest',
        'does not compare cells against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
