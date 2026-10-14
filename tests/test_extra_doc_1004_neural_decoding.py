"""Mutation and oracle tests for extra_doc.neural_decoding."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_1004_neural_decoding.py',
                        'src/sugarcode/extra_doc/neural_decoding.py')

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
    # oracle seeded with row number 1004
    assert m.read([]) == {'total': 0, 'lean': {}, 'steady': []}
    # signals 2, 4 lean even
    r = m.read([('w', 2), ('w', 4)])
    assert r == {'total': 2, 'lean': {'w': 'even'}, 'steady': []}
    # 3, 5 lean odd
    r = m.read([('w', 3), ('w', 5)])
    assert r == {'total': 2, 'lean': {'w': 'odd'}, 'steady': []}
    # 2, 3 tie and read steady
    r = m.read([('w', 2), ('w', 3)])
    assert r == {'total': 2, 'lean': {'w': 'tie'}, 'steady': ['w']}
    # 2, 2, 3 lean even
    r = m.read([('w', 2), ('w', 2), ('w', 3)])
    assert r == {'total': 3, 'lean': {'w': 'even'}, 'steady': []}
    # 3, 3, 2 lean odd
    r = m.read([('w', 3), ('w', 3), ('w', 2)])
    assert r == {'total': 3, 'lean': {'w': 'odd'}, 'steady': []}
    # 0, 1 tie: zero reads even
    r = m.read([('w', 0), ('w', 1)])
    assert r == {'total': 2, 'lean': {'w': 'tie'}, 'steady': ['w']}
    # 0, 0, 1, 1, 2 lean even
    r = m.read([('w', 0), ('w', 0), ('w', 1), ('w', 1), ('w', 2)])
    assert r == {'total': 5, 'lean': {'w': 'even'}, 'steady': []}
    # a lone 7 leans odd; a lone 4 leans even
    r = m.read([('w', 7)])
    assert r == {'total': 1, 'lean': {'w': 'odd'}, 'steady': []}
    r = m.read([('w', 4)])
    assert r == {'total': 1, 'lean': {'w': 'even'}, 'steady': []}
    # boundary signals: 10, 9 tie; 10 lone leans even; 0 lone leans even
    r = m.read([('w', 10), ('w', 9)])
    assert r['lean'] == {'w': 'tie'}
    r = m.read([('w', 10)])
    assert r['lean'] == {'w': 'even'}
    r = m.read([('w', 0)])
    assert r['lean'] == {'w': 'even'}
    # each channel keeps its own leaning
    r = m.read([('a', 2), ('b', 3), ('a', 3), ('b', 2)])
    assert r == {'total': 4, 'lean': {'a': 'tie', 'b': 'tie'},
                 'steady': ['a', 'b']}
    # dynamic equal-string witness: equal channels share one leaning
    dyn = ''.join(['w', '1'])
    r = m.read([(dyn, 2), (''.join(['w', '1']), 4)])
    assert r['lean'] == {'w1': 'even'} and r['steady'] == []
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['c%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 0), (n, 1)]
    r = m.read(rows)
    assert r['steady'] == sorted(names)
    assert r['lean'] == {n: 'tie' for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.read('nope')
    with pytest.raises(TypeError):
        m.read(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.read([('w', 1)] * 101)
    with pytest.raises(TypeError):
        m.read([('w', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.read([('w', 1), ('w',)])
    with pytest.raises(TypeError):
        m.read([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.read([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.read([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.read([('w', '1')])
    with pytest.raises(TypeError):
        m.read([('w', LyingI())])
    with pytest.raises(TypeError):
        m.read([('w', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.read([('w', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.read([('w', -1)])
    # first bad row pins, mixed failure types
    try:
        m.read([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.read([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.read({'w': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.read(ListSub([('w', 1)]))
    with pytest.raises(TypeError):
        m.read([ListSub(('w', 1))])
    # tuple rows accepted exactly like lists
    assert m.read((('w', 1),)) == m.read([('w', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.read([('w', 2), ['w', 4], ('w', 4)])
    assert mixed == m.read([['w', 2], ('w', 4), ['w', 4]])
    # boundary acceptance pins
    assert m.read([('abcdefgh', 1)])['lean'] == {'abcdefgh': 'odd'}
    assert m.read([('w', 1)] * 100)['total'] == 100
    assert m.read([('w', 0)])['lean'] == {'w': 'even'}
    assert m.read([('w', 10)])['lean'] == {'w': 'even'}
    # default-start pins: unknown channel starts with no leaning
    r = m.read([('zz', 4), ('zz', 4)])
    assert r['lean'] == {'zz': 'even'} and r['steady'] == []
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
    ('signal % 2 == 0', 'signal % 2 == 1'),
    ('signal % 2 == 0', 'signal % 2 != 0'),
    ('signal % 2 == 0', 'signal % 3 == 0'),
    ('evens += 1', 'evens += 2'),
    ('odds += 1', 'odds += 2'),
    ('evens = 0', 'evens = 1'),
    ('if evens > odds:', 'if evens >= odds:'),
    ('elif odds > evens:', 'elif odds >= evens:'),
    ("lean[channel] = 'even'", "lean[channel] = 'odd'"),
    ("lean[channel] = 'tie'", "lean[channel] = 'even'"),
    ("if side == 'tie'", "if side != 'tie'"),
    ('steady = sorted(', 'steady = list('),
    ('values.setdefault(channel, []).append(signal)',
     'values.setdefault(channel, [2]).append(signal)'),
    ('values: dict = {}', "values: dict = {'zz': [2]}"),
    ('lean = {}', "lean = {'zz': 'even'}"),
    ('channel, signal = row', 'signal, channel = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(lean)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(channel) <= MAX_NAME',
     'not 1 <= len(channel) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_SIGNAL = 0', 'MIN_SIGNAL = 1'),
    ('MAX_SIGNAL = 10', 'MAX_SIGNAL = 9'),
    ('not MIN_SIGNAL <= signal <= MAX_SIGNAL',
     'not MIN_SIGNAL < signal < MAX_SIGNAL'),
    ("'lean': lean", "'lean': steady"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.read([(S('w'), 5)]), TypeError,
           'row 1: channel must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.read('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.read(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.read({'w': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.read([('w', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.read([('w', 1), 'bad']), TypeError,
           'row 2: expected (channel, signal) tuple, got str')
    _exact(lambda: m.read([('w', 1), ('w',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.read([(1, 1)]), TypeError,
           'row 1: channel must be str, got int')
    _exact(lambda: m.read([(True, 1)]), TypeError,
           'row 1: channel must be str, got bool')
    _exact(lambda: m.read([('', 1)]), ValueError,
           'row 1: channel must be 1-8 chars')
    _exact(lambda: m.read([('abcdefghi', 1)]), ValueError,
           'row 1: channel must be 1-8 chars')
    _exact(lambda: m.read([('w', '1')]), TypeError,
           'row 1: signal must be int, got str')
    _exact(lambda: m.read([('w', True)]), TypeError,
           'row 1: signal must be int, got bool')
    _exact(lambda: m.read([('w', 11)]), ValueError,
           'row 1: signal must be 0-10, got 11')
    _exact(lambda: m.read([('w', -1)]), ValueError,
           'row 1: signal must be 0-10, got -1')
    _exact(lambda: m.read([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: channel must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 1004, Neural Decoding' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: signal bookkeeping only; no decoding model fit'
    assert module.NOT_CLAIMED == (
        'does not model firing rates',
        'does not weight signals by record order',
        'does not measure signal magnitude, only parity',
        'does not compare channels against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
