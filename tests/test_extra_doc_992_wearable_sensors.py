"""Mutation and oracle tests for extra_doc.wearable_sensors."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_992_wearable_sensors.py',
                        'src/sugarcode/extra_doc/wearable_sensors.py')

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
    # oracle seeded with row number 992
    assert m.track([]) == {'total': 0, 'peaks': {}, 'peaky': []}
    # readings 3, 5, 5, 2 peak twice
    r = m.track([('s', 3), ('s', 5), ('s', 5), ('s', 2)])
    assert r == {'total': 4, 'peaks': {'s': 2}, 'peaky': []}
    # 5, 5, 5 peak 3 times and mark peaky: boundary on the peaky side
    r = m.track([('s', 5), ('s', 5), ('s', 5)])
    assert r == {'total': 3, 'peaks': {'s': 3}, 'peaky': ['s']}
    # 1, 2 peak once
    r = m.track([('s', 1), ('s', 2)])
    assert r == {'total': 2, 'peaks': {'s': 1}, 'peaky': []}
    # 4, 5, 5 peak twice: only readings at the peak count
    r = m.track([('s', 4), ('s', 5), ('s', 5)])
    assert r == {'total': 3, 'peaks': {'s': 2}, 'peaky': []}
    # 0, 0, 0 peak 3 times at a zero peak
    r = m.track([('s', 0), ('s', 0), ('s', 0)])
    assert r == {'total': 3, 'peaks': {'s': 3}, 'peaky': ['s']}
    # 5, 1, 5 peak twice
    r = m.track([('s', 5), ('s', 1), ('s', 5)])
    assert r == {'total': 3, 'peaks': {'s': 2}, 'peaky': []}
    # 2, 2 peak twice: boundary just below peaky
    r = m.track([('s', 2), ('s', 2)])
    assert r == {'total': 2, 'peaks': {'s': 2}, 'peaky': []}
    # a lone reading peaks once
    r = m.track([('s', 7)])
    assert r == {'total': 1, 'peaks': {'s': 1}, 'peaky': []}
    # boundary readings: 10, 10, 10 peak 3 times
    r = m.track([('s', 10), ('s', 10), ('s', 10)])
    assert r['peaks'] == {'s': 3} and r['peaky'] == ['s']
    # each sensor keeps its own peak
    r = m.track([('a', 5), ('b', 5), ('a', 5), ('a', 5)])
    assert r == {'total': 4, 'peaks': {'a': 3, 'b': 1},
                 'peaky': ['a']}
    # dynamic equal-string witness: equal sensors share one peak
    dyn = ''.join(['s', '1'])
    r = m.track([(dyn, 5), (''.join(['s', '1']), 5),
                 (''.join(['s', '1']), 5)])
    assert r['peaks'] == {'s1': 3} and r['peaky'] == ['s1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['s%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 5), (n, 5), (n, 5)]
    r = m.track(rows)
    assert r['peaky'] == sorted(names)
    assert r['peaks'] == {n: 3 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.track('nope')
    with pytest.raises(TypeError):
        m.track(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.track([('s', 1)] * 101)
    with pytest.raises(TypeError):
        m.track([('s', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.track([('s', 1), ('s',)])
    with pytest.raises(TypeError):
        m.track([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.track([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.track([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.track([('s', '1')])
    with pytest.raises(TypeError):
        m.track([('s', LyingI())])
    with pytest.raises(TypeError):
        m.track([('s', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.track([('s', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.track([('s', -1)])
    # first bad row pins, mixed failure types
    try:
        m.track([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.track([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.track({'s': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.track(ListSub([('s', 1)]))
    with pytest.raises(TypeError):
        m.track([ListSub(('s', 1))])
    # tuple rows accepted exactly like lists
    assert m.track((('s', 1),)) == m.track([('s', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.track([('s', 3), ['s', 5], ('s', 5)])
    assert mixed == m.track([['s', 3], ('s', 5), ['s', 5]])
    # boundary acceptance pins
    assert m.track([('abcdefgh', 1)])['peaks'] == {'abcdefgh': 1}
    assert m.track([('s', 1)] * 100)['total'] == 100
    assert m.track([('s', 0)])['peaks'] == {'s': 1}
    assert m.track([('s', 10)])['peaks'] == {'s': 1}
    # default-start pins: unknown sensor peaks once per reading
    r = m.track([('zz', 4), ('zz', 4)])
    assert r['peaks'] == {'zz': 2} and r['peaky'] == []
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
    ('v == mx', 'v == mx - 1'),
    ('v == mx', 'v >= mx - 1'),
    ('v == mx', 'v != mx'),
    ('mx = max(vals)', 'mx = min(vals)'),
    ('mx = max(vals)', 'mx = vals[0]'),
    ('for v in vals:', 'for v in vals[1:]:'),
    ('for v in vals:', 'for v in vals[:1]:'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('count >= PEAKY', 'count > PEAKY'),
    ('count >= PEAKY', 'count >= PEAKY + 1'),
    ('PEAKY = 3', 'PEAKY = 2'),
    ('PEAKY = 3', 'PEAKY = 4'),
    ('peaky = sorted(', 'peaky = list('),
    ('values.setdefault(sensor, []).append(reading)',
     'values.setdefault(sensor, [7]).append(reading)'),
    ('values: dict = {}', "values: dict = {'zz': [3, 5]}"),
    ('peaks = {}', "peaks = {'zz': 5}"),
    ('sensor, reading = row', 'reading, sensor = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(peaks)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(sensor) <= MAX_NAME',
     'not 1 <= len(sensor) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_READING = 0', 'MIN_READING = 1'),
    ('MAX_READING = 10', 'MAX_READING = 9'),
    ('not MIN_READING <= reading <= MAX_READING',
     'not MIN_READING < reading < MAX_READING'),
    ("'peaks': peaks", "'peaks': peaky"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.track([(S('s'), 5)]), TypeError,
           'row 1: sensor must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.track('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.track(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.track({'s': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.track([('s', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.track([('s', 1), 'bad']), TypeError,
           'row 2: expected (sensor, reading) tuple, got str')
    _exact(lambda: m.track([('s', 1), ('s',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.track([(1, 1)]), TypeError,
           'row 1: sensor must be str, got int')
    _exact(lambda: m.track([(True, 1)]), TypeError,
           'row 1: sensor must be str, got bool')
    _exact(lambda: m.track([('', 1)]), ValueError,
           'row 1: sensor must be 1-8 chars')
    _exact(lambda: m.track([('abcdefghi', 1)]), ValueError,
           'row 1: sensor must be 1-8 chars')
    _exact(lambda: m.track([('s', '1')]), TypeError,
           'row 1: reading must be int, got str')
    _exact(lambda: m.track([('s', True)]), TypeError,
           'row 1: reading must be int, got bool')
    _exact(lambda: m.track([('s', 11)]), ValueError,
           'row 1: reading must be 0-10, got 11')
    _exact(lambda: m.track([('s', -1)]), ValueError,
           'row 1: reading must be 0-10, got -1')
    _exact(lambda: m.track([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: sensor must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 992, Wearable Sensors' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: reading bookkeeping only; no sampling hardware modeled'
    assert module.NOT_CLAIMED == (
        'does not model sampling rate or drift',
        'does not weight peak readings by record order',
        'does not count readings near the peak, only at it',
        'does not compare sensors against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
