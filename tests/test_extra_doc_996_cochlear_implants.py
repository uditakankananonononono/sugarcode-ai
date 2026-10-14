"""Mutation and oracle tests for extra_doc.cochlear_implants."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_996_cochlear_implants.py',
                        'src/sugarcode/extra_doc/cochlear_implants.py')

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
    # oracle seeded with row number 996
    assert m.hear([]) == {'total': 0, 'segments': {}, 'steady': []}
    # pulses 5, 5, 2, 2, 2, 5 split into 3 runs
    r = m.hear([('e', 5), ('e', 5), ('e', 2), ('e', 2), ('e', 2),
                ('e', 5)])
    assert r == {'total': 6, 'segments': {'e': 3}, 'steady': []}
    # 1, 2, 3 split into 3
    r = m.hear([('e', 1), ('e', 2), ('e', 3)])
    assert r == {'total': 3, 'segments': {'e': 3}, 'steady': []}
    # 5, 5 hold 1 run and read steady
    r = m.hear([('e', 5), ('e', 5)])
    assert r == {'total': 2, 'segments': {'e': 1}, 'steady': ['e']}
    # 1, 1, 2, 1 split into 3
    r = m.hear([('e', 1), ('e', 1), ('e', 2), ('e', 1)])
    assert r == {'total': 4, 'segments': {'e': 3}, 'steady': []}
    # 2, 2 hold 1
    r = m.hear([('e', 2), ('e', 2)])
    assert r == {'total': 2, 'segments': {'e': 1}, 'steady': ['e']}
    # 1, 2, 1, 2 split into 4
    r = m.hear([('e', 1), ('e', 2), ('e', 1), ('e', 2)])
    assert r == {'total': 4, 'segments': {'e': 4}, 'steady': []}
    # 0, 0, 10 split into 2
    r = m.hear([('e', 0), ('e', 0), ('e', 10)])
    assert r == {'total': 3, 'segments': {'e': 2}, 'steady': []}
    # a lone pulse holds 1 run
    r = m.hear([('e', 4)])
    assert r == {'total': 1, 'segments': {'e': 1}, 'steady': ['e']}
    # equal runs are not merged across other pulses: 3, 3, 1, 3, 3 -> 3
    r = m.hear([('e', 3), ('e', 3), ('e', 1), ('e', 3), ('e', 3)])
    assert r['segments'] == {'e': 3}
    # boundary pulses: 10, 10 hold 1
    r = m.hear([('e', 10), ('e', 10)])
    assert r['segments'] == {'e': 1} and r['steady'] == ['e']
    # each electrode keeps its own runs
    r = m.hear([('a', 1), ('b', 3), ('a', 1), ('b', 3)])
    assert r == {'total': 4, 'segments': {'a': 1, 'b': 1},
                 'steady': ['a', 'b']}
    # dynamic equal-string witness: equal electrodes share one count
    dyn = ''.join(['e', '1'])
    r = m.hear([(dyn, 5), (''.join(['e', '1']), 5)])
    assert r['segments'] == {'e1': 1} and r['steady'] == ['e1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['e%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 5), (n, 5)]
    r = m.hear(rows)
    assert r['steady'] == sorted(names)
    assert r['segments'] == {n: 1 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.hear('nope')
    with pytest.raises(TypeError):
        m.hear(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.hear([('e', 1)] * 101)
    with pytest.raises(TypeError):
        m.hear([('e', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.hear([('e', 1), ('e',)])
    with pytest.raises(TypeError):
        m.hear([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.hear([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.hear([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.hear([('e', '1')])
    with pytest.raises(TypeError):
        m.hear([('e', LyingI())])
    with pytest.raises(TypeError):
        m.hear([('e', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.hear([('e', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.hear([('e', -1)])
    # first bad row pins, mixed failure types
    try:
        m.hear([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.hear([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.hear({'e': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.hear(ListSub([('e', 1)]))
    with pytest.raises(TypeError):
        m.hear([ListSub(('e', 1))])
    # tuple rows accepted exactly like lists
    assert m.hear((('e', 1),)) == m.hear([('e', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.hear([('e', 5), ['e', 2], ('e', 2)])
    assert mixed == m.hear([['e', 5], ('e', 2), ['e', 2]])
    # boundary acceptance pins
    assert m.hear([('abcdefgh', 1)])['segments'] == {'abcdefgh': 1}
    assert m.hear([('e', 1)] * 100)['total'] == 100
    assert m.hear([('e', 0)])['segments'] == {'e': 1}
    assert m.hear([('e', 10)])['segments'] == {'e': 1}
    # default-start pins: unknown electrode starts with one run
    r = m.hear([('zz', 1), ('zz', 2)])
    assert r['segments'] == {'zz': 2} and r['steady'] == []
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
    ('vals[i] != vals[i - 1]', 'vals[i] == vals[i - 1]'),
    ('segs = 1', 'segs = 0'),
    ('segs = 1', 'segs = 2'),
    ('segs += 1', 'segs += 2'),
    ('range(1, len(vals))', 'range(len(vals))'),
    ('segs == 1', 'segs == 2'),
    ('segs == 1', 'segs != 1'),
    ('steady = sorted(', 'steady = list('),
    ('values.setdefault(electrode, []).append(pulse)',
     'values.setdefault(electrode, [7]).append(pulse)'),
    ('values: dict = {}', "values: dict = {'zz': [1, 2]}"),
    ('segments = {}', "segments = {'zz': 5}"),
    ('electrode, pulse = row', 'pulse, electrode = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(segments)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(electrode) <= MAX_NAME',
     'not 1 <= len(electrode) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_PULSE = 0', 'MIN_PULSE = 1'),
    ('MAX_PULSE = 10', 'MAX_PULSE = 9'),
    ('not MIN_PULSE <= pulse <= MAX_PULSE',
     'not MIN_PULSE < pulse < MAX_PULSE'),
    ("'segments': segments", "'segments': steady"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.hear([(S('e'), 5)]), TypeError,
           'row 1: electrode must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.hear('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.hear(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.hear({'e': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.hear([('e', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.hear([('e', 1), 'bad']), TypeError,
           'row 2: expected (electrode, pulse) tuple, got str')
    _exact(lambda: m.hear([('e', 1), ('e',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.hear([(1, 1)]), TypeError,
           'row 1: electrode must be str, got int')
    _exact(lambda: m.hear([(True, 1)]), TypeError,
           'row 1: electrode must be str, got bool')
    _exact(lambda: m.hear([('', 1)]), ValueError,
           'row 1: electrode must be 1-8 chars')
    _exact(lambda: m.hear([('abcdefghi', 1)]), ValueError,
           'row 1: electrode must be 1-8 chars')
    _exact(lambda: m.hear([('e', '1')]), TypeError,
           'row 1: pulse must be int, got str')
    _exact(lambda: m.hear([('e', True)]), TypeError,
           'row 1: pulse must be int, got bool')
    _exact(lambda: m.hear([('e', 11)]), ValueError,
           'row 1: pulse must be 0-10, got 11')
    _exact(lambda: m.hear([('e', -1)]), ValueError,
           'row 1: pulse must be 0-10, got -1')
    _exact(lambda: m.hear([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: electrode must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 996, Cochlear Implants' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: pulse bookkeeping only; no auditory nerve modeled'
    assert module.NOT_CLAIMED == (
        'does not model pitch mapping',
        'does not measure run lengths, only how many runs there are',
        'does not merge equal runs separated by other pulses',
        'does not compare electrodes against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
