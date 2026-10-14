"""Mutation and oracle tests for extra_doc.negative_index_materials."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_954_negative_index_materials.py',
                        'src/sugarcode/extra_doc/negative_index_materials.py')

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


def _core(module):
    m = module
    # oracle seeded with row number 954
    assert m.refract([]) == {'total': 0, 'phases': {}, 'reversed': []}
    # advance 4 lands exactly on 6: reversed
    r = m.refract([('a', 4)])
    assert r == {'total': 1, 'phases': {'a': 6}, 'reversed': ['a']}
    # advance 5 lands on 5: not reversed
    r = m.refract([('a', 5)])
    assert r == {'total': 1, 'phases': {'a': 5}, 'reversed': []}
    # backward wrap: total advance 16 lands on 6
    r = m.refract([('a', 10), ('a', 6)])
    assert r['phases'] == {'a': 6} and r['reversed'] == ['a']
    # three tens: (10 - 30) mod 12 = 4, not reversed
    r = m.refract([('a', 10), ('a', 10), ('a', 10)])
    assert r['phases'] == {'a': 4} and r['reversed'] == []
    # advance 11 wraps to 11: reversed
    r = m.refract([('a', 10), ('a', 1)])
    assert r['phases'] == {'a': 11} and r['reversed'] == ['a']
    # waves are independent
    r = m.refract([('a', 4), ('b', 5), ('c', 10), ('c', 6)])
    assert r['phases'] == {'a': 6, 'b': 5, 'c': 6}
    assert r['reversed'] == ['a', 'c']
    # dynamic equal-string witness: equal waves share one phase
    dyn = ''.join(['w', '1'])
    r = m.refract([(dyn, 3), (''.join(['w', '1']), 3)])
    assert r['phases'] == {'w1': 4} and r['reversed'] == []
    # wide many-name sort pin (20 waves at the boundary)
    names = ['wv%02d' % i for i in range(20)]
    r = m.refract([(n, 4) for n in names])
    assert r['reversed'] == sorted(names)
    assert r['phases'] == {n: 6 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.refract('nope')
    with pytest.raises(TypeError):
        m.refract(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.refract([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.refract([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.refract([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.refract([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.refract([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.refract([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.refract([('a', '1')])
    with pytest.raises(TypeError):
        m.refract([('a', LyingI())])
    with pytest.raises(TypeError):
        m.refract([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.refract([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.refract([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.refract([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.refract([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.refract({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.refract(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.refract([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.refract((('a', 1),)) == m.refract([('a', 1)])
    # boundary acceptance pins
    assert m.refract([('abcdefgh', 4)])['reversed'] == ['abcdefgh']
    assert m.refract([('a', 1)] * 100)['total'] == 100
    assert m.refract([('a', 0)])['phases'] == {'a': 10}
    assert m.refract([('a', 10)])['phases'] == {'a': 0}
    # default-start pin: unknown wave must start its advance at 0
    r = m.refract([('zz', 4)])
    assert r['phases'] == {'zz': 6} and r['reversed'] == ['zz']
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
    ('(LAUNCH_PHASE - total) % PERIOD', '(total - LAUNCH_PHASE) % PERIOD'),
    ('(LAUNCH_PHASE - total) % PERIOD', '(LAUNCH_PHASE + total) % PERIOD'),
    ('LAUNCH_PHASE = 10', 'LAUNCH_PHASE = 9'),
    ('LAUNCH_PHASE = 10', 'LAUNCH_PHASE = 11'),
    ('PERIOD = 12', 'PERIOD = 11'),
    ('PERIOD = 12', 'PERIOD = 13'),
    ('REVERSED_FROM = 6', 'REVERSED_FROM = 7'),
    ('REVERSED_FROM = 6', 'REVERSED_FROM = 5'),
    ('phase >= REVERSED_FROM', 'phase > REVERSED_FROM'),
    ('phase >= REVERSED_FROM', 'phase < REVERSED_FROM'),
    ('advances.get(wave, 0) + advance', 'advances.get(wave, 0) - advance'),
    ('advances.get(wave, 0)', 'advances.get(wave, 1)'),
    ("'total': len(rows)", "'total': len(advances)"),
    ('wave, advance = row', 'advance, wave = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MIN_ADVANCE = 0', 'MIN_ADVANCE = 1'),
    ('MAX_ADVANCE = 10', 'MAX_ADVANCE = 9'),
    ('not MIN_ADVANCE <= advance <= MAX_ADVANCE',
     'not MIN_ADVANCE < advance < MAX_ADVANCE'),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(wave) <= MAX_NAME', 'not 1 <= len(wave) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 954, Negative Index Materials' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True


class S(str):
    pass


def _exact(fn, exc_type, expected):
    with pytest.raises(exc_type) as info:
        fn()
    assert str(info.value) == expected


def test_str_subclass_rejected_v2():
    m = _load_code(SRC)
    _exact(lambda: m.refract([(S('a'), 4)]), TypeError,
           'row 1: wave must be str, got S')


def test_error_messages_exact_v2():
    m = _load_code(SRC)
    _exact(lambda: m.refract('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.refract(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.refract({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.refract([('a', 4)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.refract([('a', 4), 'bad']), TypeError,
           'row 2: expected (wave, advance) tuple, got str')
    _exact(lambda: m.refract([('a', 4), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.refract([(1, 4)]), TypeError,
           'row 1: wave must be str, got int')
    _exact(lambda: m.refract([(True, 4)]), TypeError,
           'row 1: wave must be str, got bool')
    _exact(lambda: m.refract([('', 4)]), ValueError,
           'row 1: wave must be 1-8 chars')
    _exact(lambda: m.refract([('abcdefghi', 4)]), ValueError,
           'row 1: wave must be 1-8 chars')
    _exact(lambda: m.refract([('a', '4')]), TypeError,
           'row 1: advance must be int, got str')
    _exact(lambda: m.refract([('a', True)]), TypeError,
           'row 1: advance must be int, got bool')
    _exact(lambda: m.refract([('a', 11)]), ValueError,
           'row 1: advance must be 0-10, got 11')
    _exact(lambda: m.refract([('a', -1)]), ValueError,
           'row 1: advance must be 0-10, got -1')
    _exact(lambda: m.refract([('a', 4), ('a', 4), (1, 4)]),
           TypeError, 'row 3: wave must be str, got int')


def test_scope_wording_exact_v2():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: phase bookkeeping only; no field simulation'
    assert module.NOT_CLAIMED == (
        'does not solve Maxwell equations',
        'does not model dispersion or loss',
        'does not compute ray trajectories',
        'does not model interfaces between slabs',
    )
