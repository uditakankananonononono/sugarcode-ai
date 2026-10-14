"""Mutation and oracle tests for extra_doc.tissue_engineering."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_962_tissue_engineering.py',
                        'src/sugarcode/extra_doc/tissue_engineering.py')

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
    # oracle seeded with row number 962
    assert m.merge([]) == {'total': 0, 'covered': {}, 'confluent': []}
    # touching strands cover 10 but do not merge: not confluent
    r = m.merge([('a', 0, 5), ('a', 5, 10)])
    assert r == {'total': 2, 'covered': {'a': 10}, 'confluent': []}
    # overlapping strands merge into one 0-to-10 coverage: confluent
    r = m.merge([('a', 0, 6), ('a', 4, 10)])
    assert r == {'total': 2, 'covered': {'a': 10}, 'confluent': ['a']}
    # gapped strands cover only their own lengths
    r = m.merge([('a', 2, 4), ('a', 6, 8)])
    assert r['covered'] == {'a': 4} and r['confluent'] == []
    # record order does not matter: strands are sorted before merging
    r = m.merge([('a', 4, 10), ('a', 0, 6)])
    assert r['covered'] == {'a': 10} and r['confluent'] == ['a']
    # a contained strand adds nothing
    r = m.merge([('a', 0, 10), ('a', 2, 4)])
    assert r['covered'] == {'a': 10} and r['confluent'] == ['a']
    # a single strand covers its own length, never confluent mid-field
    r = m.merge([('a', 1, 4)])
    assert r['covered'] == {'a': 3} and r['confluent'] == []
    # a single full-field strand is confluent
    r = m.merge([('a', 0, 10)])
    assert r['covered'] == {'a': 10} and r['confluent'] == ['a']
    # a chain of pairwise overlaps merges across all three
    r = m.merge([('a', 0, 3), ('a', 2, 5), ('a', 4, 6)])
    assert r['covered'] == {'a': 6}
    # a three-strand merge can reach confluence
    r = m.merge([('a', 0, 4), ('a', 3, 7), ('a', 6, 10)])
    assert r['covered'] == {'a': 10} and r['confluent'] == ['a']
    # scaffolds are tracked independently
    r = m.merge([('a', 0, 6), ('b', 1, 2), ('a', 4, 10)])
    assert r['covered'] == {'a': 10, 'b': 1}
    assert r['confluent'] == ['a']
    # dynamic equal-string witness: equal scaffolds share one strand list
    dyn = ''.join(['b', '1'])
    r = m.merge([(dyn, 0, 6), (''.join(['b', '1']), 4, 10)])
    assert r['covered'] == {'b1': 10} and r['confluent'] == ['b1']
    # wide many-name sort pin, inserted in reverse order (20 scaffolds)
    names = ['sc%02d' % i for i in range(20)]
    r = m.merge([(n, 0, 10) for n in reversed(names)])
    assert r['confluent'] == sorted(names)
    assert r['covered'] == {n: 10 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.merge('nope')
    with pytest.raises(TypeError):
        m.merge(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.merge([('a', 0, 1)] * 101)
    with pytest.raises(TypeError):
        m.merge([('a', 0, 1), 'bad'])
    with pytest.raises(ValueError, match='3 fields'):
        m.merge([('a', 0, 1), ('a', 0)])
    with pytest.raises(TypeError):
        m.merge([(1, 0, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.merge([('', 0, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.merge([('abcdefghi', 0, 1)])
    with pytest.raises(TypeError):
        m.merge([('a', '0', 1)])
    with pytest.raises(TypeError):
        m.merge([('a', LyingI(), 1)])
    with pytest.raises(TypeError):
        m.merge([('a', True, 1)])
    with pytest.raises(ValueError, match='0-10'):
        m.merge([('a', -1, 1)])
    with pytest.raises(ValueError, match='0-10'):
        m.merge([('a', 0, 11)])
    # start must be strictly below end
    with pytest.raises(ValueError, match='below end'):
        m.merge([('a', 5, 5)])
    with pytest.raises(ValueError, match='below end'):
        m.merge([('a', 7, 3)])
    # first bad row pins, mixed failure types
    try:
        m.merge([('ok', 0, 1), ('ok', 0, 1), (7, 0, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.merge([('ok', 0, 1), ('ok', 0, 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.merge({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.merge(ListSub([('a', 0, 1)]))
    with pytest.raises(TypeError):
        m.merge([ListSub(('a', 0, 1))])
    # tuple rows accepted exactly like lists
    assert m.merge((('a', 0, 1),)) == m.merge([('a', 0, 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.merge([('a', 0, 5), ['a', 4, 8]])
    assert mixed == m.merge([['a', 0, 5], ('a', 4, 8)])
    # boundary acceptance pins
    assert m.merge([('abcdefgh', 0, 1)])['covered'] == {'abcdefgh': 1}
    assert m.merge([('a', 0, 1)] * 100)['total'] == 100
    assert m.merge([('a', 9, 10)])['covered'] == {'a': 1}
    assert m.merge([('a', 0, 10)])['confluent'] == ['a']
    # default-start pin: unknown scaffold must start with no strands
    r = m.merge([('zz', 0, 2)])
    assert r['covered'] == {'zz': 2}
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
    ('start < spans[-1][1]', 'start <= spans[-1][1]'),
    ('start < spans[-1][1]', 'start > spans[-1][1]'),
    ('max(spans[-1][1], end)', 'min(spans[-1][1], end)'),
    ('max(spans[-1][1], end)', 'end'),
    ('sorted(strands[scaffold])', 'strands[scaffold]'),
    ('len(spans) == 1', 'len(spans) == 2'),
    ('if len(spans) == 1 and spans[0] == [MIN_POS, MAX_POS]:',
     'if len(spans) >= 1 and spans[0][0] == MIN_POS:'),
    ('end - start', 'end - start + 1'),
    ('if start >= end:', 'if start > end:'),
    ('MIN_POS = 0', 'MIN_POS = 1'),
    ('MAX_POS = 10', 'MAX_POS = 9'),
    ('not MIN_POS <= value <= MAX_POS',
     'not MIN_POS < value < MAX_POS'),
    ('scaffold, start, end = row', 'start, scaffold, end = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(strands)"),
    ('confluent.sort()', 'pass'),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(scaffold) <= MAX_NAME', 'not 1 <= len(scaffold) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 3', 'len(row) != 2'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.merge([(S('a'), 0, 1)]), TypeError,
           'row 1: scaffold must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.merge('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.merge(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.merge({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.merge([('a', 0, 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.merge([('a', 0, 1), 'bad']), TypeError,
           'row 2: expected (scaffold, start, end) tuple, got str')
    _exact(lambda: m.merge([('a', 0, 1), ('a', 0)]), ValueError,
           'row 2: expected 3 fields, got 2')
    _exact(lambda: m.merge([(1, 0, 1)]), TypeError,
           'row 1: scaffold must be str, got int')
    _exact(lambda: m.merge([(True, 0, 1)]), TypeError,
           'row 1: scaffold must be str, got bool')
    _exact(lambda: m.merge([('', 0, 1)]), ValueError,
           'row 1: scaffold must be 1-8 chars')
    _exact(lambda: m.merge([('abcdefghi', 0, 1)]), ValueError,
           'row 1: scaffold must be 1-8 chars')
    _exact(lambda: m.merge([('a', '0', 1)]), TypeError,
           'row 1: start must be int, got str')
    _exact(lambda: m.merge([('a', 0, '1')]), TypeError,
           'row 1: end must be int, got str')
    _exact(lambda: m.merge([('a', True, 1)]), TypeError,
           'row 1: start must be int, got bool')
    _exact(lambda: m.merge([('a', -1, 1)]), ValueError,
           'row 1: start must be 0-10, got -1')
    _exact(lambda: m.merge([('a', 0, 11)]), ValueError,
           'row 1: end must be 0-10, got 11')
    _exact(lambda: m.merge([('a', 5, 5)]), ValueError,
           'row 1: start must be below end, got 5 and 5')
    _exact(lambda: m.merge([('a', 7, 3)]), ValueError,
           'row 1: start must be below end, got 7 and 3')
    _exact(lambda: m.merge([('a', 0, 1), ('a', 0, 1), (1, 0, 1)]),
           TypeError, 'row 3: scaffold must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 962, Tissue Engineering' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: coverage bookkeeping only; '
                            'no scaffold chemistry modeled')
    assert module.NOT_CLAIMED == (
        'does not model cell growth over time',
        'does not simulate scaffold degradation',
        'does not merge strands that only touch',
        'does not track coverage outside 0 to 10',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
