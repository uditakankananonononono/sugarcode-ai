"""Mutation and oracle tests for extra_doc.neurofeedback."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_1001_neurofeedback.py',
                        'src/sugarcode/extra_doc/neurofeedback.py')

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
    # oracle seeded with row number 1001
    assert m.train([]) == {'total': 0, 'lags': {}, 'calm': []}
    # amplitudes 1, 3 lag 4
    r = m.train([('w', 1), ('w', 3)])
    assert r == {'total': 2, 'lags': {'w': 4}, 'calm': []}
    # 3, 3 lag 0 and read calm
    r = m.train([('w', 3), ('w', 3)])
    assert r == {'total': 2, 'lags': {'w': 0}, 'calm': ['w']}
    # 0, 2, 2 lag 4
    r = m.train([('w', 0), ('w', 2), ('w', 2)])
    assert r == {'total': 3, 'lags': {'w': 4}, 'calm': []}
    # 2, 3 lag 1
    r = m.train([('w', 2), ('w', 3)])
    assert r == {'total': 2, 'lags': {'w': 1}, 'calm': []}
    # 0, 3 lag 9
    r = m.train([('w', 0), ('w', 3)])
    assert r == {'total': 2, 'lags': {'w': 9}, 'calm': []}
    # 1, 2, 3 lag 5
    r = m.train([('w', 1), ('w', 2), ('w', 3)])
    assert r == {'total': 3, 'lags': {'w': 5}, 'calm': []}
    # 3, 1 lag 4
    r = m.train([('w', 3), ('w', 1)])
    assert r == {'total': 2, 'lags': {'w': 4}, 'calm': []}
    # a lone amplitude lags 0 and reads calm
    r = m.train([('w', 7)])
    assert r == {'total': 1, 'lags': {'w': 0}, 'calm': ['w']}
    # boundary amplitudes: 10, 0 lag 100; 10, 10 lag 0
    r = m.train([('w', 10), ('w', 0)])
    assert r['lags'] == {'w': 100}
    r = m.train([('w', 10), ('w', 10)])
    assert r['lags'] == {'w': 0} and r['calm'] == ['w']
    # each wave keeps its own shortfall
    r = m.train([('a', 1), ('b', 5), ('a', 3), ('b', 5)])
    assert r == {'total': 4, 'lags': {'a': 4, 'b': 0},
                 'calm': ['b']}
    # dynamic equal-string witness: equal waves share one shortfall
    dyn = ''.join(['w', '1'])
    r = m.train([(dyn, 3), (''.join(['w', '1']), 3)])
    assert r['lags'] == {'w1': 0} and r['calm'] == ['w1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['w%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 5), (n, 5)]
    r = m.train(rows)
    assert r['calm'] == sorted(names)
    assert r['lags'] == {n: 0 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.train('nope')
    with pytest.raises(TypeError):
        m.train(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.train([('w', 1)] * 101)
    with pytest.raises(TypeError):
        m.train([('w', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.train([('w', 1), ('w',)])
    with pytest.raises(TypeError):
        m.train([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.train([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.train([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.train([('w', '1')])
    with pytest.raises(TypeError):
        m.train([('w', LyingI())])
    with pytest.raises(TypeError):
        m.train([('w', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.train([('w', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.train([('w', -1)])
    # first bad row pins, mixed failure types
    try:
        m.train([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.train([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.train({'w': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.train(ListSub([('w', 1)]))
    with pytest.raises(TypeError):
        m.train([ListSub(('w', 1))])
    # tuple rows accepted exactly like lists
    assert m.train((('w', 1),)) == m.train([('w', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.train([('w', 1), ['w', 3], ('w', 3)])
    assert mixed == m.train([['w', 1], ('w', 3), ['w', 3]])
    # boundary acceptance pins
    assert m.train([('abcdefgh', 1)])['lags'] == {'abcdefgh': 0}
    assert m.train([('w', 1)] * 100)['total'] == 100
    assert m.train([('w', 0)])['lags'] == {'w': 0}
    assert m.train([('w', 10)])['lags'] == {'w': 0}
    # default-start pins: unknown wave starts with no shortfall
    r = m.train([('zz', 4), ('zz', 4)])
    assert r['lags'] == {'zz': 0} and r['calm'] == ['zz']
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
    ('(peak - v) * (peak - v)', 'peak - v'),
    ('(peak - v) * (peak - v)', '(peak - v) * v'),
    ('peak = max(vals)', 'peak = min(vals)'),
    ('peak = max(vals)', 'peak = vals[0]'),
    ('lag += (peak - v) * (peak - v)', 'lag = (peak - v) * (peak - v)'),
    ('lag = 0', 'lag = 1'),
    ('lag == 0', 'lag != 0'),
    ('lag == 0', 'lag == 1'),
    ('calm = sorted(', 'calm = list('),
    ('values.setdefault(wave, []).append(amplitude)',
     'values.setdefault(wave, [3]).append(amplitude)'),
    ('values: dict = {}', "values: dict = {'zz': [3, 1]}"),
    ('lags = {}', "lags = {'zz': 5}"),
    ('wave, amplitude = row', 'amplitude, wave = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(lags)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(wave) <= MAX_NAME',
     'not 1 <= len(wave) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_AMPLITUDE = 0', 'MIN_AMPLITUDE = 1'),
    ('MAX_AMPLITUDE = 10', 'MAX_AMPLITUDE = 9'),
    ('not MIN_AMPLITUDE <= amplitude <= MAX_AMPLITUDE',
     'not MIN_AMPLITUDE < amplitude < MAX_AMPLITUDE'),
    ("'lags': lags", "'lags': calm"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.train([(S('w'), 5)]), TypeError,
           'row 1: wave must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.train('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.train(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.train({'w': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.train([('w', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.train([('w', 1), 'bad']), TypeError,
           'row 2: expected (wave, amplitude) tuple, got str')
    _exact(lambda: m.train([('w', 1), ('w',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.train([(1, 1)]), TypeError,
           'row 1: wave must be str, got int')
    _exact(lambda: m.train([(True, 1)]), TypeError,
           'row 1: wave must be str, got bool')
    _exact(lambda: m.train([('', 1)]), ValueError,
           'row 1: wave must be 1-8 chars')
    _exact(lambda: m.train([('abcdefghi', 1)]), ValueError,
           'row 1: wave must be 1-8 chars')
    _exact(lambda: m.train([('w', '1')]), TypeError,
           'row 1: amplitude must be int, got str')
    _exact(lambda: m.train([('w', True)]), TypeError,
           'row 1: amplitude must be int, got bool')
    _exact(lambda: m.train([('w', 11)]), ValueError,
           'row 1: amplitude must be 0-10, got 11')
    _exact(lambda: m.train([('w', -1)]), ValueError,
           'row 1: amplitude must be 0-10, got -1')
    _exact(lambda: m.train([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: wave must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 1001, Neurofeedback' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: amplitude bookkeeping only; no EEG hardware modeled'
    assert module.NOT_CLAIMED == (
        'does not model frequency bands',
        'does not weight shortfalls by record order',
        'does not measure depth below the peak, only squared distance',
        'does not compare waves against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
