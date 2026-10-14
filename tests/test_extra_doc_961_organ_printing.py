"""Mutation and oracle tests for extra_doc.organ_printing."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_961_organ_printing.py',
                        'src/sugarcode/extra_doc/organ_printing.py')

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
    # oracle seeded with row number 961
    assert m.complete([]) == {'total': 0, 'complete': [], 'missing': {}}
    # layers 1, 2, 4 leave the organ missing [3]
    r = m.complete([('a', 1), ('a', 2), ('a', 4)])
    assert r == {'total': 3, 'complete': [], 'missing': {'a': [3]}}
    # all four layers complete the organ; it leaves the missing map
    r = m.complete([('a', 1), ('a', 2), ('a', 3), ('a', 4)])
    assert r == {'total': 4, 'complete': ['a'], 'missing': {}}
    # a repeated layer does not help
    r = m.complete([('a', 1), ('a', 1), ('a', 1)])
    assert r['missing'] == {'a': [2, 3, 4]}
    # missing layers are listed sorted, however the records are ordered
    r = m.complete([('a', 4), ('a', 2)])
    assert r['missing'] == {'a': [1, 3]}
    # a duplicated full set still completes
    r = m.complete([('a', 1), ('a', 1), ('a', 2), ('a', 3), ('a', 4)])
    assert r['complete'] == ['a'] and r['missing'] == {}
    # boundary layers
    r = m.complete([('a', 1), ('a', 4)])
    assert r['missing'] == {'a': [2, 3]}
    # organs are tracked independently
    r = m.complete([('b', 1), ('b', 2), ('b', 3), ('b', 4), ('a', 1)])
    assert r['complete'] == ['b'] and r['missing'] == {'a': [2, 3, 4]}
    # dynamic equal-string witness: equal organs share one layer set
    dyn = ''.join(['b', '1'])
    r = m.complete([(dyn, 1), (''.join(['b', '1']), 2),
                    (dyn, 3), (''.join(['b', '1']), 4)])
    assert r['complete'] == ['b1'] and r['missing'] == {}
    # wide many-name sort pin, inserted in reverse order (20 organs)
    names = ['or%02d' % i for i in range(20)]
    rows = [(n, layer) for n in reversed(names) for layer in (1, 2, 3, 4)]
    r = m.complete(rows)
    assert r['complete'] == sorted(names)
    assert r['missing'] == {}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.complete('nope')
    with pytest.raises(TypeError):
        m.complete(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.complete([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.complete([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.complete([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.complete([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.complete([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.complete([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.complete([('a', '1')])
    with pytest.raises(TypeError):
        m.complete([('a', LyingI())])
    with pytest.raises(TypeError):
        m.complete([('a', True)])
    with pytest.raises(ValueError, match='1-4'):
        m.complete([('a', 0)])
    with pytest.raises(ValueError, match='1-4'):
        m.complete([('a', 5)])
    # first bad row pins, mixed failure types
    try:
        m.complete([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.complete([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.complete({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.complete(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.complete([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.complete((('a', 1),)) == m.complete([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.complete([('a', 1), ['a', 2]])
    assert mixed == m.complete([['a', 1], ('a', 2)])
    # boundary acceptance pins
    assert m.complete([('abcdefgh', 1)])['missing'] == {'abcdefgh': [2, 3, 4]}
    assert m.complete([('a', 1)] * 100)['total'] == 100
    assert m.complete([('a', 1)])['missing'] == {'a': [2, 3, 4]}
    assert m.complete([('a', 4)])['missing'] == {'a': [1, 2, 3]}
    # default-start pin: unknown organ must start with an empty layer set
    r = m.complete([('zz', 1)])
    assert r['missing'] == {'zz': [2, 3, 4]}
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
    ('printed[organ] >= REQUIRED', 'printed[organ] > REQUIRED'),
    ('REQUIRED - printed[organ]', 'printed[organ] - REQUIRED'),
    ('printed.setdefault(organ, set()).add(layer)',
     'printed.setdefault(organ, set()).add(layer + 1)'),
    ('REQUIRED = frozenset({1, 2, 3, 4})', 'REQUIRED = frozenset({1, 2, 3})'),
    ('REQUIRED = frozenset({1, 2, 3, 4})', 'REQUIRED = frozenset({1, 2, 3, 4, 5})'),
    ('MIN_LAYER = 1', 'MIN_LAYER = 0'),
    ('MAX_LAYER = 4', 'MAX_LAYER = 5'),
    ('not MIN_LAYER <= layer <= MAX_LAYER',
     'not MIN_LAYER < layer < MAX_LAYER'),
    ('organ, layer = row', 'layer, organ = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(printed)"),
    ('done = sorted(', 'done = list('),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(organ) <= MAX_NAME', 'not 1 <= len(organ) < MAX_NAME'),
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
    _exact(lambda: m.complete([(S('a'), 1)]), TypeError,
           'row 1: organ must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.complete('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.complete(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.complete({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.complete([('a', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.complete([('a', 1), 'bad']), TypeError,
           'row 2: expected (organ, layer) tuple, got str')
    _exact(lambda: m.complete([('a', 1), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.complete([(1, 1)]), TypeError,
           'row 1: organ must be str, got int')
    _exact(lambda: m.complete([(True, 1)]), TypeError,
           'row 1: organ must be str, got bool')
    _exact(lambda: m.complete([('', 1)]), ValueError,
           'row 1: organ must be 1-8 chars')
    _exact(lambda: m.complete([('abcdefghi', 1)]), ValueError,
           'row 1: organ must be 1-8 chars')
    _exact(lambda: m.complete([('a', '1')]), TypeError,
           'row 1: layer must be int, got str')
    _exact(lambda: m.complete([('a', True)]), TypeError,
           'row 1: layer must be int, got bool')
    _exact(lambda: m.complete([('a', 0)]), ValueError,
           'row 1: layer must be 1-4, got 0')
    _exact(lambda: m.complete([('a', 5)]), ValueError,
           'row 1: layer must be 1-4, got 5')
    _exact(lambda: m.complete([('a', 1), ('a', 1), (1, 1)]),
           TypeError, 'row 3: organ must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 961, Organ Printing' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: layer-set bookkeeping only; '
                            'no organ biology modeled')
    assert module.NOT_CLAIMED == (
        'does not model cell placement within a layer',
        'does not simulate vascularization',
        'does not order the layers into a print sequence',
        'does not track partially printed layers',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
