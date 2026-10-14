"""Mutation and oracle tests for extra_doc.gene_therapy."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_965_gene_therapy.py',
                        'src/sugarcode/extra_doc/gene_therapy.py')

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
    # oracle seeded with row number 965
    assert m.express([]) == {'total': 0, 'medians': {}, 'stable': []}
    # 3, 5, 8 gives median 5, which is stable
    r = m.express([('a', 3), ('a', 5), ('a', 8)])
    assert r == {'total': 3, 'medians': {'a': 5}, 'stable': ['a']}
    # an even count takes the lower middle: 3, 5 gives 3, not 4
    r = m.express([('a', 3), ('a', 5)])
    assert r['medians'] == {'a': 3} and r['stable'] == []
    # a single reading is the median
    r = m.express([('a', 4)])
    assert r == {'total': 1, 'medians': {'a': 4}, 'stable': ['a']}
    # the median is computed on sorted readings, not record order
    r = m.express([('a', 8), ('a', 3), ('a', 5)])
    assert r['medians'] == {'a': 5}
    # duplicates count as readings: 5, 5, 3 gives median 5
    r = m.express([('a', 5), ('a', 5), ('a', 3)])
    assert r['medians'] == {'a': 5}
    # the band edges 4 and 6 are stable, 3 and 7 are not
    assert m.express([('a', 4)])['stable'] == ['a']
    assert m.express([('a', 6)])['stable'] == ['a']
    assert m.express([('a', 3)])['stable'] == []
    assert m.express([('a', 7)])['stable'] == []
    # boundary expressions
    r = m.express([('a', 0), ('a', 10)])
    assert r['medians'] == {'a': 0}
    # patients are tracked independently
    r = m.express([('a', 5), ('b', 9), ('a', 5), ('b', 9)])
    assert r['medians'] == {'a': 5, 'b': 9}
    assert r['stable'] == ['a']
    # dynamic equal-string witness: equal patients share one reading list
    dyn = ''.join(['b', '1'])
    r = m.express([(dyn, 3), (''.join(['b', '1']), 5), (dyn, 8)])
    assert r['medians'] == {'b1': 5}
    # wide many-name sort pin, inserted in reverse order (20 patients)
    names = ['pt%02d' % i for i in range(20)]
    r = m.express([(n, 5) for n in reversed(names)])
    assert r['stable'] == sorted(names)
    assert r['medians'] == {n: 5 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.express('nope')
    with pytest.raises(TypeError):
        m.express(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.express([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.express([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.express([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.express([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.express([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.express([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.express([('a', '1')])
    with pytest.raises(TypeError):
        m.express([('a', LyingI())])
    with pytest.raises(TypeError):
        m.express([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.express([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.express([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.express([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.express([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.express({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.express(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.express([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.express((('a', 1),)) == m.express([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.express([('a', 5), ['a', 3]])
    assert mixed == m.express([['a', 5], ('a', 3)])
    # boundary acceptance pins
    assert m.express([('abcdefgh', 1)])['medians'] == {'abcdefgh': 1}
    assert m.express([('a', 1)] * 100)['total'] == 100
    assert m.express([('a', 0)])['medians'] == {'a': 0}
    assert m.express([('a', 10)])['medians'] == {'a': 10}
    # default-start pin: unknown patient must start with no readings
    r = m.express([('zz', 7)])
    assert r['medians'] == {'zz': 7}
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
    ('(len(values) - 1) // 2', 'len(values) // 2'),
    ('(len(values) - 1) // 2', '(len(values) - 1) // 3'),
    ('sorted(values)', 'values'),
    ('BAND_LOW <= median <= BAND_HIGH', 'BAND_LOW < median < BAND_HIGH'),
    ('BAND_LOW = 4', 'BAND_LOW = 5'),
    ('BAND_HIGH = 6', 'BAND_HIGH = 5'),
    ('readings.setdefault(patient, []).append(expression)',
     'readings.setdefault(patient, []).append(expression + 1)'),
    ('stable = sorted(', 'stable = list('),
    ('MIN_EXPRESSION = 0', 'MIN_EXPRESSION = 1'),
    ('MAX_EXPRESSION = 10', 'MAX_EXPRESSION = 9'),
    ('not MIN_EXPRESSION <= expression <= MAX_EXPRESSION',
     'not MIN_EXPRESSION < expression < MAX_EXPRESSION'),
    ('patient, expression = row', 'expression, patient = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(readings)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(patient) <= MAX_NAME', 'not 1 <= len(patient) < MAX_NAME'),
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
    _exact(lambda: m.express([(S('a'), 5)]), TypeError,
           'row 1: patient must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.express('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.express(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.express({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.express([('a', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.express([('a', 1), 'bad']), TypeError,
           'row 2: expected (patient, expression) tuple, got str')
    _exact(lambda: m.express([('a', 1), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.express([(1, 1)]), TypeError,
           'row 1: patient must be str, got int')
    _exact(lambda: m.express([(True, 1)]), TypeError,
           'row 1: patient must be str, got bool')
    _exact(lambda: m.express([('', 1)]), ValueError,
           'row 1: patient must be 1-8 chars')
    _exact(lambda: m.express([('abcdefghi', 1)]), ValueError,
           'row 1: patient must be 1-8 chars')
    _exact(lambda: m.express([('a', '1')]), TypeError,
           'row 1: expression must be int, got str')
    _exact(lambda: m.express([('a', True)]), TypeError,
           'row 1: expression must be int, got bool')
    _exact(lambda: m.express([('a', 11)]), ValueError,
           'row 1: expression must be 0-10, got 11')
    _exact(lambda: m.express([('a', -1)]), ValueError,
           'row 1: expression must be 0-10, got -1')
    _exact(lambda: m.express([('a', 1), ('a', 1), (1, 1)]),
           TypeError, 'row 3: patient must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 965, Gene Therapy' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: median bookkeeping only; '
                            'no gene regulation modeled')
    assert module.NOT_CLAIMED == (
        'does not model expression over time',
        'does not compute a mean or mode',
        'does not take the upper middle on even counts',
        'does not adjust readings toward the median',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
