"""Mutation and oracle tests for extra_doc.deep_brain_stimulation."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_998_deep_brain_stimulation.py',
                        'src/sugarcode/extra_doc/deep_brain_stimulation.py')

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
    # oracle seeded with row number 998
    assert m.stimulate([]) == {'total': 0, 'climbs': {}, 'rising': []}
    # pulses 1, 2, 3, 2, 3 climb to 3
    r = m.stimulate([('r', 1), ('r', 2), ('r', 3), ('r', 2), ('r', 3)])
    assert r == {'total': 5, 'climbs': {'r': 3}, 'rising': ['r']}
    # 5, 5, 5 climb to 1 since equal pulses do not climb
    r = m.stimulate([('r', 5), ('r', 5), ('r', 5)])
    assert r == {'total': 3, 'climbs': {'r': 1}, 'rising': []}
    # 1, 2, 1, 2, 3 climb to 3
    r = m.stimulate([('r', 1), ('r', 2), ('r', 1), ('r', 2), ('r', 3)])
    assert r == {'total': 5, 'climbs': {'r': 3}, 'rising': ['r']}
    # 3, 2, 1 climb to 1
    r = m.stimulate([('r', 3), ('r', 2), ('r', 1)])
    assert r == {'total': 3, 'climbs': {'r': 1}, 'rising': []}
    # 1, 3, 2 climb to 2
    r = m.stimulate([('r', 1), ('r', 3), ('r', 2)])
    assert r == {'total': 3, 'climbs': {'r': 2}, 'rising': []}
    # 1, 1, 2 climb to 2: the equal opening breaks strictness
    r = m.stimulate([('r', 1), ('r', 1), ('r', 2)])
    assert r == {'total': 3, 'climbs': {'r': 2}, 'rising': []}
    # 1, 2, 2 climb to 2: the equal ending breaks strictness
    r = m.stimulate([('r', 1), ('r', 2), ('r', 2)])
    assert r == {'total': 3, 'climbs': {'r': 2}, 'rising': []}
    # 2, 2 climb to 1
    r = m.stimulate([('r', 2), ('r', 2)])
    assert r == {'total': 2, 'climbs': {'r': 1}, 'rising': []}
    # a lone pulse climbs to 1
    r = m.stimulate([('r', 7)])
    assert r == {'total': 1, 'climbs': {'r': 1}, 'rising': []}
    # 1, 2 climb to 2: boundary just below rising
    r = m.stimulate([('r', 1), ('r', 2)])
    assert r == {'total': 2, 'climbs': {'r': 2}, 'rising': []}
    # boundary pulses: 0, 1, 2 climb to 3; 10, 10 climb to 1
    r = m.stimulate([('r', 0), ('r', 1), ('r', 2)])
    assert r['climbs'] == {'r': 3} and r['rising'] == ['r']
    r = m.stimulate([('r', 10), ('r', 10)])
    assert r['climbs'] == {'r': 1}
    # each region keeps its own climb
    r = m.stimulate([('a', 1), ('b', 5), ('a', 2), ('a', 3)])
    assert r == {'total': 4, 'climbs': {'a': 3, 'b': 1},
                 'rising': ['a']}
    # dynamic equal-string witness: equal regions share one climb
    dyn = ''.join(['r', '1'])
    r = m.stimulate([(dyn, 1), (''.join(['r', '1']), 2),
                     (''.join(['r', '1']), 3)])
    assert r['climbs'] == {'r1': 3} and r['rising'] == ['r1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['r%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 2), (n, 3)]
    r = m.stimulate(rows)
    assert r['rising'] == sorted(names)
    assert r['climbs'] == {n: 3 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.stimulate('nope')
    with pytest.raises(TypeError):
        m.stimulate(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.stimulate([('r', 1)] * 101)
    with pytest.raises(TypeError):
        m.stimulate([('r', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.stimulate([('r', 1), ('r',)])
    with pytest.raises(TypeError):
        m.stimulate([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.stimulate([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.stimulate([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.stimulate([('r', '1')])
    with pytest.raises(TypeError):
        m.stimulate([('r', LyingI())])
    with pytest.raises(TypeError):
        m.stimulate([('r', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.stimulate([('r', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.stimulate([('r', -1)])
    # first bad row pins, mixed failure types
    try:
        m.stimulate([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.stimulate([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.stimulate({'r': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.stimulate(ListSub([('r', 1)]))
    with pytest.raises(TypeError):
        m.stimulate([ListSub(('r', 1))])
    # tuple rows accepted exactly like lists
    assert m.stimulate((('r', 1),)) == m.stimulate([('r', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.stimulate([('r', 1), ['r', 2], ('r', 3)])
    assert mixed == m.stimulate([['r', 1], ('r', 2), ['r', 3]])
    # boundary acceptance pins
    assert m.stimulate([('abcdefgh', 1)])['climbs'] == {'abcdefgh': 1}
    assert m.stimulate([('r', 1)] * 100)['total'] == 100
    assert m.stimulate([('r', 0)])['climbs'] == {'r': 1}
    assert m.stimulate([('r', 10)])['climbs'] == {'r': 1}
    # default-start pins: unknown region starts with a climb of 1
    r = m.stimulate([('zz', 1), ('zz', 2)])
    assert r['climbs'] == {'zz': 2} and r['rising'] == []
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
    ('vals[i] > vals[i - 1]', 'vals[i] >= vals[i - 1]'),
    ('vals[i] > vals[i - 1]', 'vals[i] < vals[i - 1]'),
    ('run += 1', 'run += 2'),
    ('run = 1', 'run = 0'),
    ('best = 1', 'best = 0'),
    ('best = max(best, run)', 'best = run'),
    ('range(1, len(vals))', 'range(len(vals))'),
    ('best >= RISING', 'best > RISING'),
    ('best >= RISING', 'best >= RISING + 1'),
    ('RISING = 3', 'RISING = 2'),
    ('RISING = 3', 'RISING = 4'),
    ('rising = sorted(', 'rising = list('),
    ('values.setdefault(region, []).append(pulse)',
     'values.setdefault(region, [0]).append(pulse)'),
    ('values: dict = {}', "values: dict = {'zz': [1, 2, 3]}"),
    ('climbs = {}', "climbs = {'zz': 5}"),
    ('region, pulse = row', 'pulse, region = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(climbs)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(region) <= MAX_NAME',
     'not 1 <= len(region) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_PULSE = 0', 'MIN_PULSE = 1'),
    ('MAX_PULSE = 10', 'MAX_PULSE = 9'),
    ('not MIN_PULSE <= pulse <= MAX_PULSE',
     'not MIN_PULSE < pulse < MAX_PULSE'),
    ("'climbs': climbs", "'climbs': rising"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.stimulate([(S('r'), 5)]), TypeError,
           'row 1: region must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.stimulate('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.stimulate(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.stimulate({'r': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.stimulate([('r', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.stimulate([('r', 1), 'bad']), TypeError,
           'row 2: expected (region, pulse) tuple, got str')
    _exact(lambda: m.stimulate([('r', 1), ('r',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.stimulate([(1, 1)]), TypeError,
           'row 1: region must be str, got int')
    _exact(lambda: m.stimulate([(True, 1)]), TypeError,
           'row 1: region must be str, got bool')
    _exact(lambda: m.stimulate([('', 1)]), ValueError,
           'row 1: region must be 1-8 chars')
    _exact(lambda: m.stimulate([('abcdefghi', 1)]), ValueError,
           'row 1: region must be 1-8 chars')
    _exact(lambda: m.stimulate([('r', '1')]), TypeError,
           'row 1: pulse must be int, got str')
    _exact(lambda: m.stimulate([('r', True)]), TypeError,
           'row 1: pulse must be int, got bool')
    _exact(lambda: m.stimulate([('r', 11)]), ValueError,
           'row 1: pulse must be 0-10, got 11')
    _exact(lambda: m.stimulate([('r', -1)]), ValueError,
           'row 1: pulse must be 0-10, got -1')
    _exact(lambda: m.stimulate([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: region must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 998, Deep Brain Stimulation' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: pulse bookkeeping only; no neural circuitry modeled'
    assert module.NOT_CLAIMED == (
        'does not model electrode impedance',
        'does not count equal pulses as climbing',
        'does not merge climbs across a flat or falling pulse',
        'does not compare regions against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
