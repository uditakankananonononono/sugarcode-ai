"""Mutation and oracle tests for extra_doc.probiotic_design."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_982_probiotic_design.py',
                        'src/sugarcode/extra_doc/probiotic_design.py')

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
    # oracle seeded with row number 982
    assert m.brew([]) == {'total': 0, 'loads': {}, 'light': []}
    # doses 3, 4 load 9 + 16 = 25 and stay light
    r = m.brew([('c', 3), ('c', 4)])
    assert r == {'total': 2, 'loads': {'c': 25}, 'light': ['c']}
    # 4, 4 load 32 and tip over
    r = m.brew([('c', 4), ('c', 4)])
    assert r == {'total': 2, 'loads': {'c': 32}, 'light': []}
    # 5, 2, 1 load exactly 30 and hold the edge
    r = m.brew([('c', 5), ('c', 2), ('c', 1)])
    assert r == {'total': 3, 'loads': {'c': 30}, 'light': ['c']}
    # 5, 2, 1, 1 load 31, one past the edge
    r = m.brew([('c', 5), ('c', 2), ('c', 1), ('c', 1)])
    assert r['loads'] == {'c': 31} and r['light'] == []
    # a lone dose loads its own square
    r = m.brew([('c', 6)])
    assert r == {'total': 1, 'loads': {'c': 36}, 'light': []}
    # squaring makes big doses count more: 5, 1 loads 26
    r = m.brew([('c', 5), ('c', 1)])
    assert r['loads'] == {'c': 26}
    # while 3, 3 loads 18
    r = m.brew([('c', 3), ('c', 3)])
    assert r['loads'] == {'c': 18} and r['light'] == ['c']
    # a zero dose loads nothing
    r = m.brew([('c', 0), ('c', 0)])
    assert r['loads'] == {'c': 0} and r['light'] == ['c']
    # each culture keeps its own load
    r = m.brew([('a', 4), ('b', 1), ('a', 4), ('b', 1)])
    assert r == {'total': 4, 'loads': {'a': 32, 'b': 2}, 'light': ['b']}
    # boundary doses
    r = m.brew([('c', 10)])
    assert r['loads'] == {'c': 100} and r['light'] == []
    # dynamic equal-string witness: equal cultures share one load
    dyn = ''.join(['c', '1'])
    r = m.brew([(dyn, 3), (''.join(['c', '1']), 4)])
    assert r['loads'] == {'c1': 25} and r['light'] == ['c1']
    # wide many-name sort pin, inserted in reverse order (20 cultures)
    names = ['c%02d' % i for i in range(20)]
    r = m.brew([(n, 2) for n in reversed(names)])
    assert r['light'] == sorted(names)
    assert r['loads'] == {n: 4 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.brew('nope')
    with pytest.raises(TypeError):
        m.brew(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.brew([('c', 1)] * 101)
    with pytest.raises(TypeError):
        m.brew([('c', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.brew([('c', 1), ('c',)])
    with pytest.raises(TypeError):
        m.brew([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.brew([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.brew([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.brew([('c', '1')])
    with pytest.raises(TypeError):
        m.brew([('c', LyingI())])
    with pytest.raises(TypeError):
        m.brew([('c', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.brew([('c', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.brew([('c', -1)])
    # first bad row pins, mixed failure types
    try:
        m.brew([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.brew([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.brew({'c': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.brew(ListSub([('c', 1)]))
    with pytest.raises(TypeError):
        m.brew([ListSub(('c', 1))])
    # tuple rows accepted exactly like lists
    assert m.brew((('c', 1),)) == m.brew([('c', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.brew([('c', 3), ['c', 4]])
    assert mixed == m.brew([['c', 3], ('c', 4)])
    # boundary acceptance pins
    assert m.brew([('abcdefgh', 1)])['loads'] == {'abcdefgh': 1}
    assert m.brew([('c', 1)] * 100)['total'] == 100
    assert m.brew([('c', 0)])['loads'] == {'c': 0}
    assert m.brew([('c', 10)])['loads'] == {'c': 100}
    # default-start pins: unknown culture starts with no load
    r = m.brew([('zz', 3), ('zz', 4)])
    assert r['loads'] == {'zz': 25} and r['light'] == ['zz']
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
    ('loads[culture] += dose * dose', 'loads[culture] += dose * 2'),
    ('loads[culture] += dose * dose', 'loads[culture] += dose'),
    ('loads[culture] += dose * dose', 'loads[culture] = dose * dose'),
    ('loads[culture] += dose * dose', 'loads[culture] += dose * dose + 1'),
    ('loads[culture] = 0', 'loads[culture] = 1'),
    ('if culture not in loads:', 'if culture in loads:'),
    ('load <= LIGHT', 'load < LIGHT'),
    ('LIGHT = 30', 'LIGHT = 29'),
    ('LIGHT = 30', 'LIGHT = 31'),
    ('light = sorted(', 'light = list('),
    ('MIN_DOSE = 0', 'MIN_DOSE = 1'),
    ('MAX_DOSE = 10', 'MAX_DOSE = 9'),
    ('not MIN_DOSE <= dose <= MAX_DOSE',
     'not MIN_DOSE < dose < MAX_DOSE'),
    ('culture, dose = row', 'dose, culture = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(loads)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(culture) <= MAX_NAME',
     'not 1 <= len(culture) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'loads': loads", "'loads': {c: 0 for c in loads}"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.brew([(S('c'), 5)]), TypeError,
           'row 1: culture must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.brew('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.brew(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.brew({'c': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.brew([('c', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.brew([('c', 1), 'bad']), TypeError,
           'row 2: expected (culture, dose) tuple, got str')
    _exact(lambda: m.brew([('c', 1), ('c',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.brew([(1, 1)]), TypeError,
           'row 1: culture must be str, got int')
    _exact(lambda: m.brew([(True, 1)]), TypeError,
           'row 1: culture must be str, got bool')
    _exact(lambda: m.brew([('', 1)]), ValueError,
           'row 1: culture must be 1-8 chars')
    _exact(lambda: m.brew([('abcdefghi', 1)]), ValueError,
           'row 1: culture must be 1-8 chars')
    _exact(lambda: m.brew([('c', '1')]), TypeError,
           'row 1: dose must be int, got str')
    _exact(lambda: m.brew([('c', True)]), TypeError,
           'row 1: dose must be int, got bool')
    _exact(lambda: m.brew([('c', 11)]), ValueError,
           'row 1: dose must be 0-10, got 11')
    _exact(lambda: m.brew([('c', -1)]), ValueError,
           'row 1: dose must be 0-10, got -1')
    _exact(lambda: m.brew([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: culture must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 982, Probiotic Design' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: dose bookkeeping only; no fermentation modeled'
    assert module.NOT_CLAIMED == (
        'does not model bacterial growth',
        'does not weight doses by record order',
        'does not compare cultures against each other',
        'does not cap the load during accumulation',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
