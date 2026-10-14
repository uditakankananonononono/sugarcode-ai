"""Mutation and oracle tests for extra_doc.stem_cell_therapy."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_964_stem_cell_therapy.py',
                        'src/sugarcode/extra_doc/stem_cell_therapy.py')

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
    # oracle seeded with row number 964
    assert m.engraft([]) == {'total': 0, 'peak': {}, 'engrafted': []}
    # 4, 6, 5 sums to exactly 15 and engrafts
    r = m.engraft([('a', 4), ('a', 6), ('a', 5)])
    assert r == {'total': 3, 'peak': {'a': 15}, 'engrafted': ['a']}
    # 4, 5, 5 sums to 14 and does not
    r = m.engraft([('a', 4), ('a', 5), ('a', 5)])
    assert r['peak'] == {'a': 14} and r['engrafted'] == []
    # fewer than 3 records: no window, no peak
    r = m.engraft([('a', 10), ('a', 10)])
    assert r == {'total': 2, 'peak': {}, 'engrafted': []}
    # the peak is the best window, not the total: total is 20 here
    r = m.engraft([('a', 1), ('a', 9), ('a', 9), ('a', 1)])
    assert r['peak'] == {'a': 19}
    # the window slides: only the last three records reach 20
    r = m.engraft([('a', 10), ('a', 0), ('a', 0), ('a', 10), ('a', 10)])
    assert r['peak'] == {'a': 20} and r['engrafted'] == ['a']
    # boundary counts
    r = m.engraft([('a', 10), ('a', 10), ('a', 10)])
    assert r['peak'] == {'a': 30} and r['engrafted'] == ['a']
    r = m.engraft([('a', 0), ('a', 0), ('a', 0)])
    assert r['peak'] == {'a': 0} and r['engrafted'] == []
    # patients are tracked independently
    r = m.engraft([('a', 5), ('b', 0), ('a', 5), ('b', 0), ('a', 5), ('b', 0)])
    assert r['peak'] == {'a': 15, 'b': 0}
    assert r['engrafted'] == ['a']
    # dynamic equal-string witness: equal patients share one count list
    dyn = ''.join(['b', '1'])
    r = m.engraft([(dyn, 10), (''.join(['b', '1']), 10), (dyn, 10)])
    assert r['peak'] == {'b1': 30} and r['engrafted'] == ['b1']
    # wide many-name sort pin, inserted in reverse order (20 patients)
    names = ['pt%02d' % i for i in range(20)]
    rows = [(n, 10) for n in reversed(names) for _ in range(3)]
    r = m.engraft(rows)
    assert r['engrafted'] == sorted(names)
    assert r['peak'] == {n: 30 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.engraft('nope')
    with pytest.raises(TypeError):
        m.engraft(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.engraft([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.engraft([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.engraft([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.engraft([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.engraft([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.engraft([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.engraft([('a', '1')])
    with pytest.raises(TypeError):
        m.engraft([('a', LyingI())])
    with pytest.raises(TypeError):
        m.engraft([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.engraft([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.engraft([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.engraft([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.engraft([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.engraft({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.engraft(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.engraft([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.engraft((('a', 1),)) == m.engraft([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.engraft([('a', 5), ['a', 5]])
    assert mixed == m.engraft([['a', 5], ('a', 5)])
    # boundary acceptance pins
    assert m.engraft([('abcdefgh', 1)])['peak'] == {}
    assert m.engraft([('a', 1)] * 100)['total'] == 100
    assert m.engraft([('a', 0), ('a', 0), ('a', 0)])['peak'] == {'a': 0}
    assert m.engraft([('a', 10)] * 3)['peak'] == {'a': 30}
    # default-start pin: unknown patient must start with no counts
    r = m.engraft([('zz', 10), ('zz', 10), ('zz', 10)])
    assert r['peak'] == {'zz': 30}
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
    ('len(values) >= WINDOW', 'len(values) > WINDOW'),
    ('best >= ENGRAFT_LEVEL', 'best > ENGRAFT_LEVEL'),
    ('WINDOW = 3', 'WINDOW = 2'),
    ('WINDOW = 3', 'WINDOW = 4'),
    ('ENGRAFT_LEVEL = 15', 'ENGRAFT_LEVEL = 14'),
    ('ENGRAFT_LEVEL = 15', 'ENGRAFT_LEVEL = 16'),
    ('peak[patient] = max(', 'peak[patient] = min('),
    ('sum(values[start:start + WINDOW])', 'sum(values)'),
    ('range(len(values) - WINDOW + 1)', 'range(len(values) - WINDOW)'),
    ('counts.setdefault(patient, []).append(cells)',
     'counts.setdefault(patient, []).append(cells + 1)'),
    ('engrafted = sorted(', 'engrafted = list('),
    ('MIN_CELLS = 0', 'MIN_CELLS = 1'),
    ('MAX_CELLS = 10', 'MAX_CELLS = 9'),
    ('not MIN_CELLS <= cells <= MAX_CELLS',
     'not MIN_CELLS < cells < MAX_CELLS'),
    ('patient, cells = row', 'cells, patient = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(counts)"),
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
    _exact(lambda: m.engraft([(S('a'), 5)]), TypeError,
           'row 1: patient must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.engraft('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.engraft(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.engraft({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.engraft([('a', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.engraft([('a', 1), 'bad']), TypeError,
           'row 2: expected (patient, cells) tuple, got str')
    _exact(lambda: m.engraft([('a', 1), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.engraft([(1, 1)]), TypeError,
           'row 1: patient must be str, got int')
    _exact(lambda: m.engraft([(True, 1)]), TypeError,
           'row 1: patient must be str, got bool')
    _exact(lambda: m.engraft([('', 1)]), ValueError,
           'row 1: patient must be 1-8 chars')
    _exact(lambda: m.engraft([('abcdefghi', 1)]), ValueError,
           'row 1: patient must be 1-8 chars')
    _exact(lambda: m.engraft([('a', '1')]), TypeError,
           'row 1: cells must be int, got str')
    _exact(lambda: m.engraft([('a', True)]), TypeError,
           'row 1: cells must be int, got bool')
    _exact(lambda: m.engraft([('a', 11)]), ValueError,
           'row 1: cells must be 0-10, got 11')
    _exact(lambda: m.engraft([('a', -1)]), ValueError,
           'row 1: cells must be 0-10, got -1')
    _exact(lambda: m.engraft([('a', 1), ('a', 1), (1, 1)]),
           TypeError, 'row 3: patient must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 964, Stem Cell Therapy' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: window bookkeeping only; '
                            'no cell biology modeled')
    assert module.NOT_CLAIMED == (
        'does not model differentiation',
        'does not weight the days within a window',
        'does not slide windows of any other size',
        'does not predict counts beyond the records',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
