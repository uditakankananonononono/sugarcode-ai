"""Mutation and oracle tests for extra_doc.neural_encoding."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_1005_neural_encoding.py',
                        'src/sugarcode/extra_doc/neural_encoding.py')

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
    # oracle seeded with row number 1005
    assert m.write([]) == {'total': 0, 'inner': {}, 'sealed': []}
    # pulses 2, 3, 4, 5 hold 2 inside
    r = m.write([('w', 2), ('w', 3), ('w', 4), ('w', 5)])
    assert r == {'total': 4, 'inner': {'w': 2}, 'sealed': []}
    # 5, 1, 8, 2 hold 0 and read sealed
    r = m.write([('w', 5), ('w', 1), ('w', 8), ('w', 2)])
    assert r == {'total': 4, 'inner': {'w': 0}, 'sealed': ['w']}
    # 3, 3 hold 0 and read sealed
    r = m.write([('w', 3), ('w', 3)])
    assert r == {'total': 2, 'inner': {'w': 0}, 'sealed': ['w']}
    # a lone pulse holds 0
    r = m.write([('w', 7)])
    assert r == {'total': 1, 'inner': {'w': 0}, 'sealed': ['w']}
    # 1, 5, 3, 5 hold 1
    r = m.write([('w', 1), ('w', 5), ('w', 3), ('w', 5)])
    assert r == {'total': 4, 'inner': {'w': 1}, 'sealed': []}
    # 2, 2, 7, 2 hold 0
    r = m.write([('w', 2), ('w', 2), ('w', 7), ('w', 2)])
    assert r == {'total': 4, 'inner': {'w': 0}, 'sealed': ['w']}
    # 1, 2, 3, 4 hold 2
    r = m.write([('w', 1), ('w', 2), ('w', 3), ('w', 4)])
    assert r == {'total': 4, 'inner': {'w': 2}, 'sealed': []}
    # 5, 1, 3, 2 hold 1
    r = m.write([('w', 5), ('w', 1), ('w', 3), ('w', 2)])
    assert r == {'total': 4, 'inner': {'w': 1}, 'sealed': []}
    # 2, 8, 3 hold 0 and read sealed
    r = m.write([('w', 2), ('w', 8), ('w', 3)])
    assert r == {'total': 3, 'inner': {'w': 0}, 'sealed': ['w']}
    # boundary pulses: 0, 10 hold 0; 0, 5, 10 hold 1
    r = m.write([('w', 0), ('w', 10)])
    assert r['inner'] == {'w': 0} and r['sealed'] == ['w']
    r = m.write([('w', 0), ('w', 5), ('w', 10)])
    assert r['inner'] == {'w': 1} and r['sealed'] == []
    # each site keeps its own interior
    r = m.write([('a', 1), ('b', 5), ('a', 5), ('b', 5)])
    assert r == {'total': 4, 'inner': {'a': 0, 'b': 0},
                 'sealed': ['a', 'b']}
    # dynamic equal-string witness: equal sites share one interior
    dyn = ''.join(['w', '1'])
    r = m.write([(dyn, 2), (''.join(['w', '1']), 4)])
    assert r['inner'] == {'w1': 0} and r['sealed'] == ['w1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['s%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 3), (n, 5), (n, 3)]
    r = m.write(rows)
    assert r['sealed'] == sorted(names)
    assert r['inner'] == {n: 0 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.write('nope')
    with pytest.raises(TypeError):
        m.write(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.write([('w', 1)] * 101)
    with pytest.raises(TypeError):
        m.write([('w', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.write([('w', 1), ('w',)])
    with pytest.raises(TypeError):
        m.write([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.write([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.write([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.write([('w', '1')])
    with pytest.raises(TypeError):
        m.write([('w', LyingI())])
    with pytest.raises(TypeError):
        m.write([('w', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.write([('w', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.write([('w', -1)])
    # first bad row pins, mixed failure types
    try:
        m.write([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.write([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.write({'w': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.write(ListSub([('w', 1)]))
    with pytest.raises(TypeError):
        m.write([ListSub(('w', 1))])
    # tuple rows accepted exactly like lists
    assert m.write((('w', 1),)) == m.write([('w', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.write([('w', 2), ['w', 4], ('w', 4)])
    assert mixed == m.write([['w', 2], ('w', 4), ['w', 4]])
    # boundary acceptance pins
    assert m.write([('abcdefgh', 1)])['inner'] == {'abcdefgh': 0}
    assert m.write([('w', 1)] * 100)['total'] == 100
    assert m.write([('w', 0)])['inner'] == {'w': 0}
    assert m.write([('w', 10)])['inner'] == {'w': 0}
    # default-start pins: unknown site starts with no interior
    r = m.write([('zz', 4), ('zz', 4)])
    assert r['inner'] == {'zz': 0} and r['sealed'] == ['zz']
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
    ('lo = min(vals[0], vals[-1])', 'lo = min(vals)'),
    ('lo = min(vals[0], vals[-1])', 'lo = max(vals[0], vals[-1])'),
    ('hi = max(vals[0], vals[-1])', 'hi = max(vals)'),
    ('hi = max(vals[0], vals[-1])', 'hi = min(vals[0], vals[-1])'),
    ('lo < v < hi', 'lo <= v < hi'),
    ('lo < v < hi', 'lo < v <= hi'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('count == 0', 'count != 0'),
    ('count == 0', 'count == 1'),
    ('sealed = sorted(', 'sealed = list('),
    ('values.setdefault(site, []).append(pulse)',
     'values.setdefault(site, [5]).append(pulse)'),
    ('values: dict = {}', "values: dict = {'zz': [3, 1]}"),
    ('inner = {}', "inner = {'zz': 5}"),
    ('site, pulse = row', 'pulse, site = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(inner)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(site) <= MAX_NAME',
     'not 1 <= len(site) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_PULSE = 0', 'MIN_PULSE = 1'),
    ('MAX_PULSE = 10', 'MAX_PULSE = 9'),
    ('not MIN_PULSE <= pulse <= MAX_PULSE',
     'not MIN_PULSE < pulse < MAX_PULSE'),
    ("'inner': inner", "'inner': sealed"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.write([(S('w'), 5)]), TypeError,
           'row 1: site must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.write('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.write(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.write({'w': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.write([('w', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.write([('w', 1), 'bad']), TypeError,
           'row 2: expected (site, pulse) tuple, got str')
    _exact(lambda: m.write([('w', 1), ('w',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.write([(1, 1)]), TypeError,
           'row 1: site must be str, got int')
    _exact(lambda: m.write([(True, 1)]), TypeError,
           'row 1: site must be str, got bool')
    _exact(lambda: m.write([('', 1)]), ValueError,
           'row 1: site must be 1-8 chars')
    _exact(lambda: m.write([('abcdefghi', 1)]), ValueError,
           'row 1: site must be 1-8 chars')
    _exact(lambda: m.write([('w', '1')]), TypeError,
           'row 1: pulse must be int, got str')
    _exact(lambda: m.write([('w', True)]), TypeError,
           'row 1: pulse must be int, got bool')
    _exact(lambda: m.write([('w', 11)]), ValueError,
           'row 1: pulse must be 0-10, got 11')
    _exact(lambda: m.write([('w', -1)]), ValueError,
           'row 1: pulse must be 0-10, got -1')
    _exact(lambda: m.write([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: site must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 1005, Neural Encoding' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: pulse bookkeeping only; no stimulation hardware modeled'
    assert module.NOT_CLAIMED == (
        'does not model pulse timing',
        'does not weight pulses by position beyond the endpoints',
        'does not measure distance outside the endpoint span',
        'does not compare sites against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
