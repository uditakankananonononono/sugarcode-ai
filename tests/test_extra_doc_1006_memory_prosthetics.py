"""Mutation and oracle tests for extra_doc.memory_prosthetics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_1006_memory_prosthetics.py',
                        'src/sugarcode/extra_doc/memory_prosthetics.py')

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
    # oracle seeded with row number 1006
    assert m.recall([]) == {'total': 0, 'drift': {}, 'even': []}
    # cues 1, 2, 3, 4 drift 4
    r = m.recall([('w', 1), ('w', 2), ('w', 3), ('w', 4)])
    assert r == {'total': 4, 'drift': {'w': 4}, 'even': []}
    # 2, 2, 2, 2 drift 0 and read even
    r = m.recall([('w', 2), ('w', 2), ('w', 2), ('w', 2)])
    assert r == {'total': 4, 'drift': {'w': 0}, 'even': ['w']}
    # 1, 5, 1 drift 0: the middle cue joins neither half
    r = m.recall([('w', 1), ('w', 5), ('w', 1)])
    assert r == {'total': 3, 'drift': {'w': 0}, 'even': ['w']}
    # 2, 3, 4 drift 2
    r = m.recall([('w', 2), ('w', 3), ('w', 4)])
    assert r == {'total': 3, 'drift': {'w': 2}, 'even': []}
    # a lone cue drifts 0
    r = m.recall([('w', 7)])
    assert r == {'total': 1, 'drift': {'w': 0}, 'even': ['w']}
    # 0, 10, 0, 10 drift 0
    r = m.recall([('w', 0), ('w', 10), ('w', 0), ('w', 10)])
    assert r == {'total': 4, 'drift': {'w': 0}, 'even': ['w']}
    # 1, 1, 1, 1, 9 drift 8
    r = m.recall([('w', 1), ('w', 1), ('w', 1), ('w', 1), ('w', 9)])
    assert r == {'total': 5, 'drift': {'w': 8}, 'even': []}
    # 6, 4, 2 drift 4
    r = m.recall([('w', 6), ('w', 4), ('w', 2)])
    assert r == {'total': 3, 'drift': {'w': 4}, 'even': []}
    # 0, 0, 1 drift 1
    r = m.recall([('w', 0), ('w', 0), ('w', 1)])
    assert r == {'total': 3, 'drift': {'w': 1}, 'even': []}
    # boundary cues: a lone 10 drifts 0; 10, 0 drift 10
    r = m.recall([('w', 10)])
    assert r['drift'] == {'w': 0}
    r = m.recall([('w', 10), ('w', 0)])
    assert r['drift'] == {'w': 10}
    # each trace keeps its own drift
    r = m.recall([('a', 1), ('b', 9), ('a', 4), ('b', 9)])
    assert r == {'total': 4, 'drift': {'a': 3, 'b': 0},
                 'even': ['b']}
    # dynamic equal-string witness: equal traces share one drift
    dyn = ''.join(['w', '1'])
    r = m.recall([(dyn, 2), (''.join(['w', '1']), 4)])
    assert r['drift'] == {'w1': 2} and r['even'] == []
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['t%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 3), (n, 5), (n, 3)]
    r = m.recall(rows)
    assert r['even'] == sorted(names)
    assert r['drift'] == {n: 0 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.recall('nope')
    with pytest.raises(TypeError):
        m.recall(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.recall([('w', 1)] * 101)
    with pytest.raises(TypeError):
        m.recall([('w', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.recall([('w', 1), ('w',)])
    with pytest.raises(TypeError):
        m.recall([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.recall([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.recall([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.recall([('w', '1')])
    with pytest.raises(TypeError):
        m.recall([('w', LyingI())])
    with pytest.raises(TypeError):
        m.recall([('w', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.recall([('w', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.recall([('w', -1)])
    # first bad row pins, mixed failure types
    try:
        m.recall([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.recall([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.recall({'w': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.recall(ListSub([('w', 1)]))
    with pytest.raises(TypeError):
        m.recall([ListSub(('w', 1))])
    # tuple rows accepted exactly like lists
    assert m.recall((('w', 1),)) == m.recall([('w', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.recall([('w', 2), ['w', 4], ('w', 4)])
    assert mixed == m.recall([['w', 2], ('w', 4), ['w', 4]])
    # boundary acceptance pins
    assert m.recall([('abcdefgh', 1)])['drift'] == {'abcdefgh': 0}
    assert m.recall([('w', 1)] * 100)['total'] == 100
    assert m.recall([('w', 0)])['drift'] == {'w': 0}
    assert m.recall([('w', 10)])['drift'] == {'w': 0}
    # default-start pins: unknown trace starts with no drift
    r = m.recall([('zz', 4), ('zz', 4)])
    assert r['drift'] == {'zz': 0} and r['even'] == ['zz']
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
    ('half = len(vals) // 2', 'half = len(vals) // 3'),
    ('half = len(vals) // 2', 'half = len(vals) / 2'),
    ('front = sum(vals[:half])', 'front = sum(vals[:half + 1])'),
    ('front = sum(vals[:half])', 'front = sum(vals[half:])'),
    ('back = sum(vals[len(vals) - half:])',
     'back = sum(vals[half:])'),
    ('back = sum(vals[len(vals) - half:])',
     'back = sum(vals[:half])'),
    ('drift[trace] = abs(front - back)',
     'drift[trace] = front - back'),
    ('drift[trace] = abs(front - back)',
     'drift[trace] = abs(front + back)'),
    ('gap == 0', 'gap != 0'),
    ('gap == 0', 'gap == 1'),
    ('even = sorted(', 'even = list('),
    ('values.setdefault(trace, []).append(cue)',
     'values.setdefault(trace, [5]).append(cue)'),
    ('values: dict = {}', "values: dict = {'zz': [3, 1]}"),
    ('drift = {}', "drift = {'zz': 5}"),
    ('trace, cue = row', 'cue, trace = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(drift)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(trace) <= MAX_NAME',
     'not 1 <= len(trace) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_CUE = 0', 'MIN_CUE = 1'),
    ('MAX_CUE = 10', 'MAX_CUE = 9'),
    ('not MIN_CUE <= cue <= MAX_CUE',
     'not MIN_CUE < cue < MAX_CUE'),
    ("'drift': drift", "'drift': even"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.recall([(S('w'), 5)]), TypeError,
           'row 1: trace must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.recall('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.recall(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.recall({'w': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.recall([('w', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.recall([('w', 1), 'bad']), TypeError,
           'row 2: expected (trace, cue) tuple, got str')
    _exact(lambda: m.recall([('w', 1), ('w',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.recall([(1, 1)]), TypeError,
           'row 1: trace must be str, got int')
    _exact(lambda: m.recall([(True, 1)]), TypeError,
           'row 1: trace must be str, got bool')
    _exact(lambda: m.recall([('', 1)]), ValueError,
           'row 1: trace must be 1-8 chars')
    _exact(lambda: m.recall([('abcdefghi', 1)]), ValueError,
           'row 1: trace must be 1-8 chars')
    _exact(lambda: m.recall([('w', '1')]), TypeError,
           'row 1: cue must be int, got str')
    _exact(lambda: m.recall([('w', True)]), TypeError,
           'row 1: cue must be int, got bool')
    _exact(lambda: m.recall([('w', 11)]), ValueError,
           'row 1: cue must be 0-10, got 11')
    _exact(lambda: m.recall([('w', -1)]), ValueError,
           'row 1: cue must be 0-10, got -1')
    _exact(lambda: m.recall([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: trace must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 1006, Memory Prosthetics' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: cue bookkeeping only; no prosthetic device modeled'
    assert module.NOT_CLAIMED == (
        'does not model consolidation over time',
        'does not weight the middle cue when the count is odd',
        'does not measure which half is heavier, only the gap',
        'does not compare traces against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
