"""Mutation and oracle tests for extra_doc.brain_computer_interfaces."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_994_brain_computer_interfaces.py',
                        'src/sugarcode/extra_doc/brain_computer_interfaces.py')

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
    # oracle seeded with row number 994
    assert m.link([]) == {'total': 0, 'tangles': {}, 'smooth': []}
    # signals 1, 2, 3 tangle 0 and read smooth
    r = m.link([('c', 1), ('c', 2), ('c', 3)])
    assert r == {'total': 3, 'tangles': {'c': 0}, 'smooth': ['c']}
    # 1, 1 tangle 0 since equal signals do not tangle
    r = m.link([('c', 1), ('c', 1)])
    assert r == {'total': 2, 'tangles': {'c': 0}, 'smooth': ['c']}
    # 3, 2, 1 tangle 3
    r = m.link([('c', 3), ('c', 2), ('c', 1)])
    assert r == {'total': 3, 'tangles': {'c': 3}, 'smooth': []}
    # 2, 1, 2 tangle 1
    r = m.link([('c', 2), ('c', 1), ('c', 2)])
    assert r == {'total': 3, 'tangles': {'c': 1}, 'smooth': []}
    # 3, 1, 2 tangle 2: every pair counts, not only neighbours
    r = m.link([('c', 3), ('c', 1), ('c', 2)])
    assert r == {'total': 3, 'tangles': {'c': 2}, 'smooth': []}
    # 2, 2, 1 tangle 2
    r = m.link([('c', 2), ('c', 2), ('c', 1)])
    assert r == {'total': 3, 'tangles': {'c': 2}, 'smooth': []}
    # 1, 2, 1 tangle 1
    r = m.link([('c', 1), ('c', 2), ('c', 1)])
    assert r == {'total': 3, 'tangles': {'c': 1}, 'smooth': []}
    # 10, 0 tangle 1
    r = m.link([('c', 10), ('c', 0)])
    assert r == {'total': 2, 'tangles': {'c': 1}, 'smooth': []}
    # a lone signal tangles 0
    r = m.link([('c', 7)])
    assert r == {'total': 1, 'tangles': {'c': 0}, 'smooth': ['c']}
    # boundary signals: 0, 10 tangle 0
    r = m.link([('c', 0), ('c', 10)])
    assert r['tangles'] == {'c': 0} and r['smooth'] == ['c']
    # each channel keeps its own tangles
    r = m.link([('a', 3), ('b', 1), ('a', 1), ('b', 2)])
    assert r == {'total': 4, 'tangles': {'a': 1, 'b': 0},
                 'smooth': ['b']}
    # dynamic equal-string witness: equal channels share one count
    dyn = ''.join(['c', '1'])
    r = m.link([(dyn, 3), (''.join(['c', '1']), 1),
                (''.join(['c', '1']), 2)])
    assert r['tangles'] == {'c1': 2} and r['smooth'] == []
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['c%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 2)]
    r = m.link(rows)
    assert r['smooth'] == sorted(names)
    assert r['tangles'] == {n: 0 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.link('nope')
    with pytest.raises(TypeError):
        m.link(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.link([('c', 1)] * 101)
    with pytest.raises(TypeError):
        m.link([('c', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.link([('c', 1), ('c',)])
    with pytest.raises(TypeError):
        m.link([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.link([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.link([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.link([('c', '1')])
    with pytest.raises(TypeError):
        m.link([('c', LyingI())])
    with pytest.raises(TypeError):
        m.link([('c', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.link([('c', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.link([('c', -1)])
    # first bad row pins, mixed failure types
    try:
        m.link([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.link([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.link({'c': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.link(ListSub([('c', 1)]))
    with pytest.raises(TypeError):
        m.link([ListSub(('c', 1))])
    # tuple rows accepted exactly like lists
    assert m.link((('c', 1),)) == m.link([('c', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.link([('c', 3), ['c', 1], ('c', 2)])
    assert mixed == m.link([['c', 3], ('c', 1), ['c', 2]])
    # boundary acceptance pins
    assert m.link([('abcdefgh', 1)])['tangles'] == {'abcdefgh': 0}
    assert m.link([('c', 1)] * 100)['total'] == 100
    assert m.link([('c', 0)])['tangles'] == {'c': 0}
    assert m.link([('c', 10)])['tangles'] == {'c': 0}
    # default-start pins: unknown channel starts with no tangles
    r = m.link([('zz', 2), ('zz', 1)])
    assert r['tangles'] == {'zz': 1} and r['smooth'] == []
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
    ('a > b', 'a >= b'),
    ('a > b', 'a < b'),
    ('a > b', 'a == b'),
    ('count == 0', 'count == 1'),
    ('count == 0', 'count <= 1'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('for b in vals[i + 1:]:', 'for b in vals:'),
    ('for i, a in enumerate(vals):', 'for i, a in enumerate(vals, 1):'),
    ('smooth = sorted(', 'smooth = list('),
    ('values.setdefault(channel, []).append(signal)',
     'values.setdefault(channel, [3]).append(signal)'),
    ('values: dict = {}', "values: dict = {'zz': [3, 1]}"),
    ('tangles = {}', "tangles = {'zz': 5}"),
    ('channel, signal = row', 'signal, channel = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(tangles)"),
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
    ("'tangles': tangles", "'tangles': smooth"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.link([(S('c'), 5)]), TypeError,
           'row 1: channel must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.link('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.link(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.link({'c': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.link([('c', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.link([('c', 1), 'bad']), TypeError,
           'row 2: expected (channel, signal) tuple, got str')
    _exact(lambda: m.link([('c', 1), ('c',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.link([(1, 1)]), TypeError,
           'row 1: channel must be str, got int')
    _exact(lambda: m.link([(True, 1)]), TypeError,
           'row 1: channel must be str, got bool')
    _exact(lambda: m.link([('', 1)]), ValueError,
           'row 1: channel must be 1-8 chars')
    _exact(lambda: m.link([('abcdefghi', 1)]), ValueError,
           'row 1: channel must be 1-8 chars')
    _exact(lambda: m.link([('c', '1')]), TypeError,
           'row 1: signal must be int, got str')
    _exact(lambda: m.link([('c', True)]), TypeError,
           'row 1: signal must be int, got bool')
    _exact(lambda: m.link([('c', 11)]), ValueError,
           'row 1: signal must be 0-10, got 11')
    _exact(lambda: m.link([('c', -1)]), ValueError,
           'row 1: signal must be 0-10, got -1')
    _exact(lambda: m.link([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: channel must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 994, Brain-Computer Interfaces' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: signal bookkeeping only; no neural decoding modeled'
    assert module.NOT_CLAIMED == (
        'does not model electrode placement',
        'does not count only consecutive drops; every pair counts',
        'does not weight tangles by how far signals drop',
        'does not compare channels against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
