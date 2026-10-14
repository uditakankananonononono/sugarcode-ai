"""Mutation and oracle tests for extra_doc.implantable_devices."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_993_implantable_devices.py',
                        'src/sugarcode/extra_doc/implantable_devices.py')

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
    # oracle seeded with row number 993
    assert m.monitor([]) == {'total': 0, 'checks': {}, 'aligned': []}
    # readings 1, 2, 3 check 3 times and align
    r = m.monitor([('d', 1), ('d', 2), ('d', 3)])
    assert r == {'total': 3, 'checks': {'d': 3}, 'aligned': ['d']}
    # 2, 2, 2 check once: only position 2 matches
    r = m.monitor([('d', 2), ('d', 2), ('d', 2)])
    assert r == {'total': 3, 'checks': {'d': 1}, 'aligned': []}
    # 1, 1, 3 check twice and align: boundary on the aligned side
    r = m.monitor([('d', 1), ('d', 1), ('d', 3)])
    assert r == {'total': 3, 'checks': {'d': 2}, 'aligned': ['d']}
    # 3, 2, 1 check once
    r = m.monitor([('d', 3), ('d', 2), ('d', 1)])
    assert r == {'total': 3, 'checks': {'d': 1}, 'aligned': []}
    # 2, 1 check 0
    r = m.monitor([('d', 2), ('d', 1)])
    assert r == {'total': 2, 'checks': {'d': 0}, 'aligned': []}
    # 0, 2 check once since 0 never matches its 1-based position
    r = m.monitor([('d', 0), ('d', 2)])
    assert r == {'total': 2, 'checks': {'d': 1}, 'aligned': []}
    # 5, 5, 5, 5, 5 check once
    r = m.monitor([('d', 5), ('d', 5), ('d', 5), ('d', 5), ('d', 5)])
    assert r == {'total': 5, 'checks': {'d': 1}, 'aligned': []}
    # a lone 1 checks once; a lone 0 checks 0
    r = m.monitor([('d', 1)])
    assert r == {'total': 1, 'checks': {'d': 1}, 'aligned': []}
    r = m.monitor([('d', 0)])
    assert r == {'total': 1, 'checks': {'d': 0}, 'aligned': []}
    # 1, 2 check 2 and align: boundary just at aligned
    r = m.monitor([('d', 1), ('d', 2)])
    assert r == {'total': 2, 'checks': {'d': 2}, 'aligned': ['d']}
    # each device keeps its own positions
    r = m.monitor([('a', 1), ('b', 2), ('a', 2), ('b', 2)])
    assert r == {'total': 4, 'checks': {'a': 2, 'b': 1},
                 'aligned': ['a']}
    # dynamic equal-string witness: equal devices share one sequence
    dyn = ''.join(['d', '1'])
    r = m.monitor([(dyn, 1), (''.join(['d', '1']), 2)])
    assert r['checks'] == {'d1': 2} and r['aligned'] == ['d1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['d%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 2)]
    r = m.monitor(rows)
    assert r['aligned'] == sorted(names)
    assert r['checks'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.monitor('nope')
    with pytest.raises(TypeError):
        m.monitor(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.monitor([('d', 1)] * 101)
    with pytest.raises(TypeError):
        m.monitor([('d', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.monitor([('d', 1), ('d',)])
    with pytest.raises(TypeError):
        m.monitor([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.monitor([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.monitor([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.monitor([('d', '1')])
    with pytest.raises(TypeError):
        m.monitor([('d', LyingI())])
    with pytest.raises(TypeError):
        m.monitor([('d', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.monitor([('d', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.monitor([('d', -1)])
    # first bad row pins, mixed failure types
    try:
        m.monitor([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.monitor([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.monitor({'d': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.monitor(ListSub([('d', 1)]))
    with pytest.raises(TypeError):
        m.monitor([ListSub(('d', 1))])
    # tuple rows accepted exactly like lists
    assert m.monitor((('d', 1),)) == m.monitor([('d', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.monitor([('d', 1), ['d', 2], ('d', 3)])
    assert mixed == m.monitor([['d', 1], ('d', 2), ['d', 3]])
    # boundary acceptance pins
    assert m.monitor([('abcdefgh', 1)])['checks'] == {'abcdefgh': 1}
    assert m.monitor([('d', 1)] * 100)['total'] == 100
    assert m.monitor([('d', 0)])['checks'] == {'d': 0}
    assert m.monitor([('d', 10)])['checks'] == {'d': 0}
    # default-start pins: unknown device starts with no matches
    r = m.monitor([('zz', 1), ('zz', 1)])
    assert r['checks'] == {'zz': 1} and r['aligned'] == []
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
    ('enumerate(vals, 1)', 'enumerate(vals)'),
    ('v == pos', 'v == pos + 1'),
    ('v == pos', 'v >= pos'),
    ('v == pos', 'v != pos'),
    ('v == pos', 'v > pos'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('count >= ALIGNED', 'count > ALIGNED'),
    ('count >= ALIGNED', 'count >= ALIGNED + 1'),
    ('ALIGNED = 2', 'ALIGNED = 1'),
    ('ALIGNED = 2', 'ALIGNED = 3'),
    ('aligned = sorted(', 'aligned = list('),
    ('values.setdefault(device, []).append(reading)',
     'values.setdefault(device, [1]).append(reading)'),
    ('values: dict = {}', "values: dict = {'zz': [1, 2]}"),
    ('checks = {}', "checks = {'zz': 5}"),
    ('device, reading = row', 'reading, device = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(checks)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(device) <= MAX_NAME',
     'not 1 <= len(device) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_READING = 0', 'MIN_READING = 1'),
    ('MAX_READING = 10', 'MAX_READING = 9'),
    ('not MIN_READING <= reading <= MAX_READING',
     'not MIN_READING < reading < MAX_READING'),
    ("'checks': checks", "'checks': aligned"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.monitor([(S('d'), 5)]), TypeError,
           'row 1: device must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.monitor('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.monitor(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.monitor({'d': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.monitor([('d', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.monitor([('d', 1), 'bad']), TypeError,
           'row 2: expected (device, reading) tuple, got str')
    _exact(lambda: m.monitor([('d', 1), ('d',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.monitor([(1, 1)]), TypeError,
           'row 1: device must be str, got int')
    _exact(lambda: m.monitor([(True, 1)]), TypeError,
           'row 1: device must be str, got bool')
    _exact(lambda: m.monitor([('', 1)]), ValueError,
           'row 1: device must be 1-8 chars')
    _exact(lambda: m.monitor([('abcdefghi', 1)]), ValueError,
           'row 1: device must be 1-8 chars')
    _exact(lambda: m.monitor([('d', '1')]), TypeError,
           'row 1: reading must be int, got str')
    _exact(lambda: m.monitor([('d', True)]), TypeError,
           'row 1: reading must be int, got bool')
    _exact(lambda: m.monitor([('d', 11)]), ValueError,
           'row 1: reading must be 0-10, got 11')
    _exact(lambda: m.monitor([('d', -1)]), ValueError,
           'row 1: reading must be 0-10, got -1')
    _exact(lambda: m.monitor([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: device must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 993, Implantable Devices' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: reading bookkeeping only; no implant hardware modeled'
    assert module.NOT_CLAIMED == (
        'does not model battery or telemetry',
        'does not weight readings by how far they miss',
        'does not compare positions across devices',
        'does not cap how many readings one device may hold',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
