"""Mutation and oracle tests for extra_doc.printing_4d."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_959_printing_4d.py',
                        'src/sugarcode/extra_doc/printing_4d.py')

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
    # oracle seeded with row number 959
    assert m.settle([]) == {'total': 0, 'lows': {}, 'floor': {}}
    # 5, 3, 3, 1 settles at 5, 3, and 1: three lows, floor 1
    r = m.settle([('a', 5), ('a', 3), ('a', 3), ('a', 1)])
    assert r == {'total': 4, 'lows': {'a': 3}, 'floor': {'a': 1}}
    # a repeat of the current floor does not count
    r = m.settle([('a', 3), ('a', 3)])
    assert r['lows'] == {'a': 1} and r['floor'] == {'a': 3}
    # a single record is always exactly one low
    r = m.settle([('a', 7)])
    assert r == {'total': 1, 'lows': {'a': 1}, 'floor': {'a': 7}}
    # a higher extension after a low is not a low
    r = m.settle([('a', 3), ('a', 9)])
    assert r['lows'] == {'a': 1} and r['floor'] == {'a': 3}
    # a new low after an increase counts again
    r = m.settle([('a', 5), ('a', 9), ('a', 2)])
    assert r['lows'] == {'a': 2} and r['floor'] == {'a': 2}
    # boundary extensions
    r = m.settle([('a', 10), ('a', 0)])
    assert r['lows'] == {'a': 2} and r['floor'] == {'a': 0}
    # panels settle independently
    r = m.settle([('a', 5), ('b', 5), ('a', 4), ('b', 6)])
    assert r['lows'] == {'a': 2, 'b': 1}
    assert r['floor'] == {'a': 4, 'b': 5}
    # dynamic equal-string witness: equal panels share one floor
    dyn = ''.join(['b', '1'])
    r = m.settle([(dyn, 5), (''.join(['b', '1']), 3)])
    assert r['lows'] == {'b1': 2} and r['floor'] == {'b1': 3}
    # wide many-name pin (20 panels, one record each)
    names = ['pn%02d' % i for i in range(20)]
    r = m.settle([(n, 7) for n in names])
    assert r['lows'] == {n: 1 for n in names}
    assert r['floor'] == {n: 7 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.settle('nope')
    with pytest.raises(TypeError):
        m.settle(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.settle([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.settle([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.settle([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.settle([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.settle([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.settle([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.settle([('a', '1')])
    with pytest.raises(TypeError):
        m.settle([('a', LyingI())])
    with pytest.raises(TypeError):
        m.settle([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.settle([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.settle([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.settle([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.settle([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.settle({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.settle(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.settle([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.settle(((('a', 1),))) == m.settle([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.settle([('a', 5), ['a', 3]])
    assert mixed == m.settle([['a', 5], ('a', 3)])
    # boundary acceptance pins
    assert m.settle([('abcdefgh', 1)])['floor'] == {'abcdefgh': 1}
    assert m.settle([('a', 1)] * 100)['total'] == 100
    assert m.settle([('a', 0)])['floor'] == {'a': 0}
    assert m.settle([('a', 10)])['floor'] == {'a': 10}
    # default-start pin: unknown panel must start the low count at 0
    r = m.settle([('zz', 0)])
    assert r['lows'] == {'zz': 1} and r['floor'] == {'zz': 0}
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
    ('extension < floor[panel]', 'extension <= floor[panel]'),
    ('extension < floor[panel]', 'extension > floor[panel]'),
    ('panel not in floor or extension < floor[panel]',
     'panel not in floor and extension < floor[panel]'),
    ('lows.get(panel, 0)', 'lows.get(panel, 1)'),
    ('lows.get(panel, 0) + 1', 'lows.get(panel, 0) + 2'),
    ('MIN_EXTENSION = 0', 'MIN_EXTENSION = 1'),
    ('MAX_EXTENSION = 10', 'MAX_EXTENSION = 9'),
    ('not MIN_EXTENSION <= extension <= MAX_EXTENSION',
     'not MIN_EXTENSION < extension < MAX_EXTENSION'),
    ('panel, extension = row', 'extension, panel = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(lows)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(panel) <= MAX_NAME', 'not 1 <= len(panel) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.settle([(S('a'), 5)]), TypeError,
           'row 1: panel must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.settle('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.settle(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.settle({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.settle([('a', 5)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.settle([('a', 5), 'bad']), TypeError,
           'row 2: expected (panel, extension) tuple, got str')
    _exact(lambda: m.settle([('a', 5), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.settle([(1, 5)]), TypeError,
           'row 1: panel must be str, got int')
    _exact(lambda: m.settle([(True, 5)]), TypeError,
           'row 1: panel must be str, got bool')
    _exact(lambda: m.settle([('', 5)]), ValueError,
           'row 1: panel must be 1-8 chars')
    _exact(lambda: m.settle([('abcdefghi', 5)]), ValueError,
           'row 1: panel must be 1-8 chars')
    _exact(lambda: m.settle([('a', '5')]), TypeError,
           'row 1: extension must be int, got str')
    _exact(lambda: m.settle([('a', True)]), TypeError,
           'row 1: extension must be int, got bool')
    _exact(lambda: m.settle([('a', 11)]), ValueError,
           'row 1: extension must be 0-10, got 11')
    _exact(lambda: m.settle([('a', -1)]), ValueError,
           'row 1: extension must be 0-10, got -1')
    _exact(lambda: m.settle([('a', 5), ('a', 5), (1, 5)]),
           TypeError, 'row 3: panel must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 959, 4D Printing' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: settling bookkeeping only; '
                            'no shape transformation modeled')
    assert module.NOT_CLAIMED == (
        'does not model the printed geometry',
        'does not simulate stimulus response over time',
        'does not raise a floor once set',
        'does not predict future extensions',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
