"""Mutation and oracle tests for extra_doc.theranostics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_990_theranostics.py',
                        'src/sugarcode/extra_doc/theranostics.py')

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
    # oracle seeded with row number 990
    assert m.scan([]) == {'total': 0, 'confirmed': {}, 'locked': []}
    # signals 4, 6, 4 confirm 2 pairs and lock: boundary on the lock side
    r = m.scan([('p', 4), ('p', 6), ('p', 4)])
    assert r == {'total': 3, 'confirmed': {'p': 2}, 'locked': ['p']}
    # 5, 5 confirm 1
    r = m.scan([('p', 5), ('p', 5)])
    assert r == {'total': 2, 'confirmed': {'p': 1}, 'locked': []}
    # 5, 5, 5 confirm 2 and lock
    r = m.scan([('p', 5), ('p', 5), ('p', 5)])
    assert r == {'total': 3, 'confirmed': {'p': 2}, 'locked': ['p']}
    # 10, 0 confirm 1: both boundary signals join a confirming pair
    r = m.scan([('p', 10), ('p', 0)])
    assert r == {'total': 2, 'confirmed': {'p': 1}, 'locked': []}
    r = m.scan([('p', 0), ('p', 10)])
    assert r['confirmed'] == {'p': 1}
    # 1, 2, 3 confirm 0
    r = m.scan([('p', 1), ('p', 2), ('p', 3)])
    assert r == {'total': 3, 'confirmed': {'p': 0}, 'locked': []}
    # 4, 1, 6 confirm 0 because only neighbours count
    r = m.scan([('p', 4), ('p', 1), ('p', 6)])
    assert r == {'total': 3, 'confirmed': {'p': 0}, 'locked': []}
    # 10, 10 confirm 0 since 20 overshoots; 6, 6 confirm 0 as well
    r = m.scan([('p', 10), ('p', 10)])
    assert r['confirmed'] == {'p': 0}
    r = m.scan([('p', 6), ('p', 6)])
    assert r['confirmed'] == {'p': 0}
    # a lone signal confirms 0
    r = m.scan([('p', 5)])
    assert r == {'total': 1, 'confirmed': {'p': 0}, 'locked': []}
    # 4, 6, 4, 6 confirm 3
    r = m.scan([('p', 4), ('p', 6), ('p', 4), ('p', 6)])
    assert r == {'total': 4, 'confirmed': {'p': 3}, 'locked': ['p']}
    # each probe keeps its own confirmations
    r = m.scan([('a', 4), ('b', 1), ('a', 6), ('a', 4)])
    assert r == {'total': 4, 'confirmed': {'a': 2, 'b': 0},
                 'locked': ['a']}
    # dynamic equal-string witness: equal probes share one count
    dyn = ''.join(['p', '1'])
    r = m.scan([(dyn, 4), (''.join(['p', '1']), 6),
                (''.join(['p', '1']), 4)])
    assert r['confirmed'] == {'p1': 2} and r['locked'] == ['p1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['p%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 5), (n, 5), (n, 5)]
    r = m.scan(rows)
    assert r['locked'] == sorted(names)
    assert r['confirmed'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.scan('nope')
    with pytest.raises(TypeError):
        m.scan(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.scan([('p', 1)] * 101)
    with pytest.raises(TypeError):
        m.scan([('p', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.scan([('p', 1), ('p',)])
    with pytest.raises(TypeError):
        m.scan([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.scan([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.scan([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.scan([('p', '1')])
    with pytest.raises(TypeError):
        m.scan([('p', LyingI())])
    with pytest.raises(TypeError):
        m.scan([('p', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.scan([('p', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.scan([('p', -1)])
    # first bad row pins, mixed failure types
    try:
        m.scan([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.scan([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.scan({'p': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.scan(ListSub([('p', 1)]))
    with pytest.raises(TypeError):
        m.scan([ListSub(('p', 1))])
    # tuple rows accepted exactly like lists
    assert m.scan((('p', 1),)) == m.scan([('p', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.scan([('p', 4), ['p', 6], ('p', 4)])
    assert mixed == m.scan([['p', 4], ('p', 6), ['p', 4]])
    # boundary acceptance pins
    assert m.scan([('abcdefgh', 1)])['confirmed'] == {'abcdefgh': 0}
    assert m.scan([('p', 1)] * 100)['total'] == 100
    assert m.scan([('p', 0)])['confirmed'] == {'p': 0}
    assert m.scan([('p', 10)])['confirmed'] == {'p': 0}
    # default-start pins: unknown probe starts with no confirmations
    r = m.scan([('zz', 4), ('zz', 6)])
    assert r['confirmed'] == {'zz': 1} and r['locked'] == []
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
    ('vals[i] + vals[i + 1] == PAIR', 'vals[i] + vals[i + 1] >= PAIR'),
    ('vals[i] + vals[i + 1] == PAIR', 'vals[i] + vals[i + 1] != PAIR'),
    ('vals[i] + vals[i + 1]', 'vals[i] - vals[i + 1]'),
    ('vals[i] + vals[i + 1]', 'vals[i] * vals[i + 1]'),
    ('PAIR = 10', 'PAIR = 9'),
    ('PAIR = 10', 'PAIR = 11'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('count >= LOCK', 'count > LOCK'),
    ('count >= LOCK', 'count >= LOCK + 1'),
    ('LOCK = 2', 'LOCK = 1'),
    ('LOCK = 2', 'LOCK = 3'),
    ('locked = sorted(', 'locked = list('),
    ('range(len(vals) - 1)', 'range(len(vals))'),
    ('range(len(vals) - 1)', 'range(1, len(vals) - 1)'),
    ('values.setdefault(probe, []).append(signal)',
     'values.setdefault(probe, [6]).append(signal)'),
    ('values: dict = {}', "values: dict = {'zz': [4, 6]}"),
    ('confirmed = {}', "confirmed = {'zz': 5}"),
    ('probe, signal = row', 'signal, probe = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(confirmed)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(probe) <= MAX_NAME',
     'not 1 <= len(probe) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_SIGNAL = 0', 'MIN_SIGNAL = 1'),
    ('MAX_SIGNAL = 10', 'MAX_SIGNAL = 9'),
    ('not MIN_SIGNAL <= signal <= MAX_SIGNAL',
     'not MIN_SIGNAL < signal < MAX_SIGNAL'),
    ("'confirmed': confirmed", "'confirmed': locked"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.scan([(S('p'), 5)]), TypeError,
           'row 1: probe must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.scan('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.scan(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.scan({'p': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.scan([('p', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.scan([('p', 1), 'bad']), TypeError,
           'row 2: expected (probe, signal) tuple, got str')
    _exact(lambda: m.scan([('p', 1), ('p',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.scan([(1, 1)]), TypeError,
           'row 1: probe must be str, got int')
    _exact(lambda: m.scan([(True, 1)]), TypeError,
           'row 1: probe must be str, got bool')
    _exact(lambda: m.scan([('', 1)]), ValueError,
           'row 1: probe must be 1-8 chars')
    _exact(lambda: m.scan([('abcdefghi', 1)]), ValueError,
           'row 1: probe must be 1-8 chars')
    _exact(lambda: m.scan([('p', '1')]), TypeError,
           'row 1: signal must be int, got str')
    _exact(lambda: m.scan([('p', True)]), TypeError,
           'row 1: signal must be int, got bool')
    _exact(lambda: m.scan([('p', 11)]), ValueError,
           'row 1: signal must be 0-10, got 11')
    _exact(lambda: m.scan([('p', -1)]), ValueError,
           'row 1: signal must be 0-10, got -1')
    _exact(lambda: m.scan([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: probe must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 990, Theranostics' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: signal bookkeeping only; no imaging modeled'
    assert module.NOT_CLAIMED == (
        'does not model probe decay',
        'does not count non-consecutive signal pairs',
        'does not weight confirmations by signal size',
        'does not compare probes against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
