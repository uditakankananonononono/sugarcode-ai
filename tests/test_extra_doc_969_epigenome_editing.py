"""Mutation and oracle tests for extra_doc.epigenome_editing."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_969_epigenome_editing.py',
                        'src/sugarcode/extra_doc/epigenome_editing.py')

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
    # oracle seeded with row number 969
    assert m.marks([]) == {'total': 0, 'peaks': {}, 'steady': []}
    # marks 3, -2, -2: levels 3, 1, -1; peak 3; fall 4, still steady
    r = m.marks([('g', 3), ('g', -2), ('g', -2)])
    assert r == {'total': 3, 'peaks': {'g': 3}, 'steady': ['g']}
    # marks 5 then -5 give a fall of 5 and lose steady
    r = m.marks([('g', 5), ('g', -5)])
    assert r == {'total': 2, 'peaks': {'g': 5}, 'steady': []}
    # a lone mark of 0 peaks at 0 with no fall
    r = m.marks([('g', 0)])
    assert r == {'total': 1, 'peaks': {'g': 0}, 'steady': ['g']}
    # a gene that only rises never falls
    r = m.marks([('g', 2), ('g', 3)])
    assert r['peaks'] == {'g': 5} and r['steady'] == ['g']
    # a gene that only falls from zero still peaks at 0
    r = m.marks([('g', -3)])
    assert r['peaks'] == {'g': 0} and r['steady'] == ['g']
    # a straight fall of 5 from the zero peak loses steady
    r = m.marks([('g', -5)])
    assert r['peaks'] == {'g': 0} and r['steady'] == []
    # fall of 4 after regaining a new peak stays steady
    r = m.marks([('g', 2), ('g', -4), ('g', 5)])
    assert r['peaks'] == {'g': 3} and r['steady'] == ['g']
    # the largest fall is kept, not the latest one
    r = m.marks([('g', 5), ('g', -5), ('g', 5), ('g', -4)])
    assert r['peaks'] == {'g': 5} and r['steady'] == []
    # each gene keeps its own level, peak and fall
    r = m.marks([('a', 5), ('b', -6), ('a', 0)])
    assert r == {'total': 3, 'peaks': {'a': 5, 'b': 0}, 'steady': ['a']}
    # boundary marks
    r = m.marks([('g', 9), ('g', -9)])
    assert r['peaks'] == {'g': 9} and r['steady'] == []
    # dynamic equal-string witness: equal genes share one level
    dyn = ''.join(['g', '1'])
    r = m.marks([(dyn, 3), (''.join(['g', '1']), -2)])
    assert r['peaks'] == {'g1': 3} and r['steady'] == ['g1']
    # wide many-name sort pin, inserted in reverse order (20 genes)
    names = ['g%02d' % i for i in range(20)]
    r = m.marks([(n, 0) for n in reversed(names)])
    assert r['steady'] == sorted(names)
    assert r['peaks'] == {n: 0 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.marks('nope')
    with pytest.raises(TypeError):
        m.marks(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.marks([('g', 1)] * 101)
    with pytest.raises(TypeError):
        m.marks([('g', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.marks([('g', 1), ('g',)])
    with pytest.raises(TypeError):
        m.marks([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.marks([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.marks([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.marks([('g', '1')])
    with pytest.raises(TypeError):
        m.marks([('g', LyingI())])
    with pytest.raises(TypeError):
        m.marks([('g', True)])
    with pytest.raises(ValueError, match='-9-9'):
        m.marks([('g', 10)])
    with pytest.raises(ValueError, match='-9-9'):
        m.marks([('g', -10)])
    # first bad row pins, mixed failure types
    try:
        m.marks([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.marks([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.marks({'g': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.marks(ListSub([('g', 1)]))
    with pytest.raises(TypeError):
        m.marks([ListSub(('g', 1))])
    # tuple rows accepted exactly like lists
    assert m.marks((('g', 1),)) == m.marks([('g', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.marks([('g', 5), ['g', -2]])
    assert mixed == m.marks([['g', 5], ('g', -2)])
    # boundary acceptance pins
    assert m.marks([('abcdefgh', 1)])['peaks'] == {'abcdefgh': 1}
    assert m.marks([('g', 1)] * 100)['total'] == 100
    assert m.marks([('g', 9)])['peaks'] == {'g': 9}
    assert m.marks([('g', -9)])['peaks'] == {'g': 0}
    # default-start pins: unknown gene starts level, peak and fall at 0
    r = m.marks([('zz', 3), ('zz', -2)])
    assert r['peaks'] == {'zz': 3} and r['steady'] == ['zz']
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
    ('levels.get(gene, 0) + mark', 'levels.get(gene, 0) - mark'),
    ('levels.get(gene, 0)', 'levels.get(gene, 1)'),
    ('peaks.get(gene, 0)', 'peaks.get(gene, 1)'),
    ('dips.get(gene, 0)', 'dips.get(gene, 5)'),
    ('peaks[gene] - levels[gene]', 'levels[gene] - peaks[gene]'),
    ('max(peaks.get(gene, 0), levels[gene])', 'levels[gene]'),
    ('max(dips.get(gene, 0), peaks[gene] - levels[gene])',
     'peaks[gene] - levels[gene]'),
    ('fall <= TOLERANCE', 'fall < TOLERANCE'),
    ('TOLERANCE = 4', 'TOLERANCE = 3'),
    ('TOLERANCE = 4', 'TOLERANCE = 5'),
    ('steady = sorted(', 'steady = list('),
    ('MIN_MARK = -9', 'MIN_MARK = -8'),
    ('MAX_MARK = 9', 'MAX_MARK = 8'),
    ('not MIN_MARK <= mark <= MAX_MARK',
     'not MIN_MARK < mark < MAX_MARK'),
    ('gene, mark = row', 'mark, gene = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(levels)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(gene) <= MAX_NAME', 'not 1 <= len(gene) < MAX_NAME'),
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
    _exact(lambda: m.marks([(S('g'), 5)]), TypeError,
           'row 1: gene must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.marks('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.marks(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.marks({'g': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.marks([('g', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.marks([('g', 1), 'bad']), TypeError,
           'row 2: expected (gene, mark) tuple, got str')
    _exact(lambda: m.marks([('g', 1), ('g',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.marks([(1, 1)]), TypeError,
           'row 1: gene must be str, got int')
    _exact(lambda: m.marks([(True, 1)]), TypeError,
           'row 1: gene must be str, got bool')
    _exact(lambda: m.marks([('', 1)]), ValueError,
           'row 1: gene must be 1-8 chars')
    _exact(lambda: m.marks([('abcdefghi', 1)]), ValueError,
           'row 1: gene must be 1-8 chars')
    _exact(lambda: m.marks([('g', '1')]), TypeError,
           'row 1: mark must be int, got str')
    _exact(lambda: m.marks([('g', True)]), TypeError,
           'row 1: mark must be int, got bool')
    _exact(lambda: m.marks([('g', 10)]), ValueError,
           'row 1: mark must be -9-9, got 10')
    _exact(lambda: m.marks([('g', -10)]), ValueError,
           'row 1: mark must be -9-9, got -10')
    _exact(lambda: m.marks([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: gene must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 969, Epigenome Editing' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: level bookkeeping only; no chromatin state modeled'
    assert module.NOT_CLAIMED == (
        'does not model methylation chemistry',
        'does not decay levels between records',
        'does not compare genes against each other',
        'does not bound the level itself',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
