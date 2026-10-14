"""Mutation and oracle tests for extra_doc.metabolic_engineering."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_971_metabolic_engineering.py',
                        'src/sugarcode/extra_doc/metabolic_engineering.py')

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
    # oracle seeded with row number 971
    assert m.tune([]) == {'total': 0, 'bottlenecks': {}, 'strong': []}
    # fluxes 6, 8, 7 give a bottleneck of 6 and stay strong
    r = m.tune([('p', 6), ('p', 8), ('p', 7)])
    assert r == {'total': 3, 'bottlenecks': {'p': 6}, 'strong': ['p']}
    # fluxes 6 then 4 give a bottleneck of 4 and drop strong
    r = m.tune([('p', 6), ('p', 4)])
    assert r == {'total': 2, 'bottlenecks': {'p': 4}, 'strong': []}
    # a lone flux is its own bottleneck
    r = m.tune([('p', 3)])
    assert r == {'total': 1, 'bottlenecks': {'p': 3}, 'strong': []}
    # a bottleneck of exactly 5 still counts strong
    r = m.tune([('p', 7), ('p', 5)])
    assert r['bottlenecks'] == {'p': 5} and r['strong'] == ['p']
    # the weak record may come first
    r = m.tune([('p', 4), ('p', 9)])
    assert r['bottlenecks'] == {'p': 4} and r['strong'] == []
    # each pathway keeps its own bottleneck
    r = m.tune([('a', 9), ('b', 2), ('a', 8)])
    assert r == {'total': 3, 'bottlenecks': {'a': 8, 'b': 2}, 'strong': ['a']}
    # boundary fluxes
    r = m.tune([('p', 10), ('p', 0)])
    assert r['bottlenecks'] == {'p': 0} and r['strong'] == []
    # a floor-level bottleneck of 10 stays strong
    r = m.tune([('p', 10), ('p', 10)])
    assert r['bottlenecks'] == {'p': 10} and r['strong'] == ['p']
    # dynamic equal-string witness: equal pathways share one bottleneck
    dyn = ''.join(['p', '1'])
    r = m.tune([(dyn, 8), (''.join(['p', '1']), 6)])
    assert r['bottlenecks'] == {'p1': 6} and r['strong'] == ['p1']
    # wide many-name sort pin, inserted in reverse order (20 pathways)
    names = ['p%02d' % i for i in range(20)]
    r = m.tune([(n, 5) for n in reversed(names)])
    assert r['strong'] == sorted(names)
    assert r['bottlenecks'] == {n: 5 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.tune('nope')
    with pytest.raises(TypeError):
        m.tune(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.tune([('p', 1)] * 101)
    with pytest.raises(TypeError):
        m.tune([('p', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.tune([('p', 1), ('p',)])
    with pytest.raises(TypeError):
        m.tune([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.tune([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.tune([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.tune([('p', '1')])
    with pytest.raises(TypeError):
        m.tune([('p', LyingI())])
    with pytest.raises(TypeError):
        m.tune([('p', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.tune([('p', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.tune([('p', -1)])
    # first bad row pins, mixed failure types
    try:
        m.tune([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.tune([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.tune({'p': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.tune(ListSub([('p', 1)]))
    with pytest.raises(TypeError):
        m.tune([ListSub(('p', 1))])
    # tuple rows accepted exactly like lists
    assert m.tune((('p', 1),)) == m.tune([('p', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.tune([('p', 8), ['p', 6]])
    assert mixed == m.tune([['p', 8], ('p', 6)])
    # boundary acceptance pins
    assert m.tune([('abcdefgh', 1)])['bottlenecks'] == {'abcdefgh': 1}
    assert m.tune([('p', 1)] * 100)['total'] == 100
    assert m.tune([('p', 0)])['bottlenecks'] == {'p': 0}
    assert m.tune([('p', 10)])['bottlenecks'] == {'p': 10}
    # default-start pins: unknown pathway starts from its first record
    r = m.tune([('zz', 8), ('zz', 6)])
    assert r['bottlenecks'] == {'zz': 6} and r['strong'] == ['zz']
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
    ('min(bottlenecks[pathway], flux)', 'max(bottlenecks[pathway], flux)'),
    ('min(bottlenecks[pathway], flux)', 'flux'),
    ('bottlenecks[pathway] = flux', 'bottlenecks[pathway] = 0'),
    ('if pathway not in bottlenecks:', 'if pathway in bottlenecks:'),
    ('low >= FLOOR', 'low > FLOOR'),
    ('FLOOR = 5', 'FLOOR = 4'),
    ('FLOOR = 5', 'FLOOR = 6'),
    ('strong = sorted(', 'strong = list('),
    ('MIN_FLUX = 0', 'MIN_FLUX = 1'),
    ('MAX_FLUX = 10', 'MAX_FLUX = 9'),
    ('not MIN_FLUX <= flux <= MAX_FLUX',
     'not MIN_FLUX < flux < MAX_FLUX'),
    ('pathway, flux = row', 'flux, pathway = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(bottlenecks)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(pathway) <= MAX_NAME',
     'not 1 <= len(pathway) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.tune([(S('p'), 5)]), TypeError,
           'row 1: pathway must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.tune('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.tune(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.tune({'p': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.tune([('p', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.tune([('p', 1), 'bad']), TypeError,
           'row 2: expected (pathway, flux) tuple, got str')
    _exact(lambda: m.tune([('p', 1), ('p',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.tune([(1, 1)]), TypeError,
           'row 1: pathway must be str, got int')
    _exact(lambda: m.tune([(True, 1)]), TypeError,
           'row 1: pathway must be str, got bool')
    _exact(lambda: m.tune([('', 1)]), ValueError,
           'row 1: pathway must be 1-8 chars')
    _exact(lambda: m.tune([('abcdefghi', 1)]), ValueError,
           'row 1: pathway must be 1-8 chars')
    _exact(lambda: m.tune([('p', '1')]), TypeError,
           'row 1: flux must be int, got str')
    _exact(lambda: m.tune([('p', True)]), TypeError,
           'row 1: flux must be int, got bool')
    _exact(lambda: m.tune([('p', 11)]), ValueError,
           'row 1: flux must be 0-10, got 11')
    _exact(lambda: m.tune([('p', -1)]), ValueError,
           'row 1: flux must be 0-10, got -1')
    _exact(lambda: m.tune([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: pathway must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 971, Metabolic Engineering' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: flux bookkeeping only; no reaction kinetics modeled'
    assert module.NOT_CLAIMED == (
        'does not model enzyme saturation',
        'does not weight fluxes by record order',
        'does not compare pathways against each other',
        'does not cap the flux during accumulation',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
