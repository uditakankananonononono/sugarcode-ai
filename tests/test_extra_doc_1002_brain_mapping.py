"""Mutation and oracle tests for extra_doc.brain_mapping."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_1002_brain_mapping.py',
                        'src/sugarcode/extra_doc/brain_mapping.py')

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
    # oracle seeded with row number 1002
    assert m.chart([]) == {'total': 0, 'interior': {}, 'hollow': []}
    # signals 1, 5, 3, 2 crowd 2 and read hollow
    r = m.chart([('r', 1), ('r', 5), ('r', 3), ('r', 2)])
    assert r == {'total': 4, 'interior': {'r': 2}, 'hollow': ['r']}
    # 5, 5 crowd 0
    r = m.chart([('r', 5), ('r', 5)])
    assert r == {'total': 2, 'interior': {'r': 0}, 'hollow': []}
    # 1, 2, 3 crowd 1
    r = m.chart([('r', 1), ('r', 2), ('r', 3)])
    assert r == {'total': 3, 'interior': {'r': 1}, 'hollow': []}
    # 1, 1, 2 crowd 0: the edge values never count
    r = m.chart([('r', 1), ('r', 1), ('r', 2)])
    assert r == {'total': 3, 'interior': {'r': 0}, 'hollow': []}
    # 1, 3, 3 crowd 0: the max edge never counts
    r = m.chart([('r', 1), ('r', 3), ('r', 3)])
    assert r == {'total': 3, 'interior': {'r': 0}, 'hollow': []}
    # 0, 10, 5, 5 crowd 2 and read hollow
    r = m.chart([('r', 0), ('r', 10), ('r', 5), ('r', 5)])
    assert r == {'total': 4, 'interior': {'r': 2}, 'hollow': ['r']}
    # 0, 5, 10 crowd 1: boundary just below hollow
    r = m.chart([('r', 0), ('r', 5), ('r', 10)])
    assert r == {'total': 3, 'interior': {'r': 1}, 'hollow': []}
    # a lone signal crowds 0
    r = m.chart([('r', 7)])
    assert r == {'total': 1, 'interior': {'r': 0}, 'hollow': []}
    # 0, 10, 5, 6, 7 crowd 3 and read hollow (pins threshold strictness above 2)
    r = m.chart([('r', 0), ('r', 10), ('r', 5), ('r', 6), ('r', 7)])
    assert r == {'total': 5, 'interior': {'r': 3}, 'hollow': ['r']}
    # 2, 2, 2 crowd 0
    r = m.chart([('r', 2), ('r', 2), ('r', 2)])
    assert r['interior'] == {'r': 0}
    # 1, 4, 2, 3 crowd 2: both middle values count
    r = m.chart([('r', 1), ('r', 4), ('r', 2), ('r', 3)])
    assert r['interior'] == {'r': 2} and r['hollow'] == ['r']
    # each region keeps its own middle
    r = m.chart([('a', 1), ('b', 3), ('a', 4), ('a', 2), ('b', 3)])
    assert r == {'total': 5, 'interior': {'a': 1, 'b': 0},
                 'hollow': []}
    # dynamic equal-string witness: equal regions share one count
    dyn = ''.join(['r', '1'])
    r = m.chart([(dyn, 1), (''.join(['r', '1']), 5),
                 (''.join(['r', '1']), 3), (dyn, 2)])
    assert r['interior'] == {'r1': 2} and r['hollow'] == ['r1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['r%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 0), (n, 10), (n, 5), (n, 5)]
    r = m.chart(rows)
    assert r['hollow'] == sorted(names)
    assert r['interior'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.chart('nope')
    with pytest.raises(TypeError):
        m.chart(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.chart([('r', 1)] * 101)
    with pytest.raises(TypeError):
        m.chart([('r', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.chart([('r', 1), ('r',)])
    with pytest.raises(TypeError):
        m.chart([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.chart([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.chart([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.chart([('r', '1')])
    with pytest.raises(TypeError):
        m.chart([('r', LyingI())])
    with pytest.raises(TypeError):
        m.chart([('r', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.chart([('r', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.chart([('r', -1)])
    # first bad row pins, mixed failure types
    try:
        m.chart([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.chart([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.chart({'r': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.chart(ListSub([('r', 1)]))
    with pytest.raises(TypeError):
        m.chart([ListSub(('r', 1))])
    # tuple rows accepted exactly like lists
    assert m.chart((('r', 1),)) == m.chart([('r', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.chart([('r', 1), ['r', 5], ('r', 3)])
    assert mixed == m.chart([['r', 1], ('r', 5), ['r', 3]])
    # boundary acceptance pins
    assert m.chart([('abcdefgh', 1)])['interior'] == {'abcdefgh': 0}
    assert m.chart([('r', 1)] * 100)['total'] == 100
    assert m.chart([('r', 0)])['interior'] == {'r': 0}
    assert m.chart([('r', 10)])['interior'] == {'r': 0}
    # default-start pins: unknown region starts with no interior
    r = m.chart([('zz', 4), ('zz', 4)])
    assert r['interior'] == {'zz': 0} and r['hollow'] == []
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
    ('lo < v < hi', 'lo <= v < hi'),
    ('lo < v < hi', 'lo < v <= hi'),
    ('lo < v < hi', 'lo <= v <= hi'),
    ('lo < v < hi', 'lo > v > hi'),
    ('lo = min(vals)', 'lo = max(vals)'),
    ('hi = max(vals)', 'hi = min(vals)'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('count >= HOLLOW', 'count > HOLLOW'),
    ('count >= HOLLOW', 'count >= HOLLOW + 1'),
    ('HOLLOW = 2', 'HOLLOW = 1'),
    ('HOLLOW = 2', 'HOLLOW = 3'),
    ('hollow = sorted(', 'hollow = list('),
    ('values.setdefault(region, []).append(signal)',
     'values.setdefault(region, [5]).append(signal)'),
    ('values: dict = {}', "values: dict = {'zz': [1, 5, 3]}"),
    ('interior = {}', "interior = {'zz': 5}"),
    ('region, signal = row', 'signal, region = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(interior)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(region) <= MAX_NAME',
     'not 1 <= len(region) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_SIGNAL = 0', 'MIN_SIGNAL = 1'),
    ('MAX_SIGNAL = 10', 'MAX_SIGNAL = 9'),
    ('not MIN_SIGNAL <= signal <= MAX_SIGNAL',
     'not MIN_SIGNAL < signal < MAX_SIGNAL'),
    ("'interior': interior", "'interior': hollow"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.chart([(S('r'), 5)]), TypeError,
           'row 1: region must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.chart('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.chart(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.chart({'r': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.chart([('r', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.chart([('r', 1), 'bad']), TypeError,
           'row 2: expected (region, signal) tuple, got str')
    _exact(lambda: m.chart([('r', 1), ('r',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.chart([(1, 1)]), TypeError,
           'row 1: region must be str, got int')
    _exact(lambda: m.chart([(True, 1)]), TypeError,
           'row 1: region must be str, got bool')
    _exact(lambda: m.chart([('', 1)]), ValueError,
           'row 1: region must be 1-8 chars')
    _exact(lambda: m.chart([('abcdefghi', 1)]), ValueError,
           'row 1: region must be 1-8 chars')
    _exact(lambda: m.chart([('r', '1')]), TypeError,
           'row 1: signal must be int, got str')
    _exact(lambda: m.chart([('r', True)]), TypeError,
           'row 1: signal must be int, got bool')
    _exact(lambda: m.chart([('r', 11)]), ValueError,
           'row 1: signal must be 0-10, got 11')
    _exact(lambda: m.chart([('r', -1)]), ValueError,
           'row 1: signal must be 0-10, got -1')
    _exact(lambda: m.chart([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: region must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 1002, Brain Mapping' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: signal bookkeeping only; no atlas projection modeled'
    assert module.NOT_CLAIMED == (
        'does not model coordinate systems',
        'does not count signals at the edges of the span',
        'does not weight interior signals by depth',
        'does not compare regions against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
