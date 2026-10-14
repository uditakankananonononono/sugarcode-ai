"""Mutation and oracle tests for extra_doc.antibody_design."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_975_antibody_design.py',
                        'src/sugarcode/extra_doc/antibody_design.py')

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
    # oracle seeded with row number 975
    assert m.bind([]) == {'total': 0, 'churn': {}, 'calm': []}
    # affinities 2, 5, 1 churn 3 + 4 = 7 and lose calm
    r = m.bind([('a', 2), ('a', 5), ('a', 1)])
    assert r == {'total': 3, 'churn': {'a': 7}, 'calm': []}
    # 3, 3, 3 churn 0 and stay calm
    r = m.bind([('a', 3), ('a', 3), ('a', 3)])
    assert r == {'total': 3, 'churn': {'a': 0}, 'calm': ['a']}
    # a lone record churns 0
    r = m.bind([('a', 8)])
    assert r == {'total': 1, 'churn': {'a': 0}, 'calm': ['a']}
    # a churn of exactly 4 still counts calm
    r = m.bind([('a', 1), ('a', 5)])
    assert r['churn'] == {'a': 4} and r['calm'] == ['a']
    # a churn of 5 spills over
    r = m.bind([('a', 1), ('a', 6)])
    assert r['churn'] == {'a': 5} and r['calm'] == []
    # the order matters: 1, 5, 2 churns 7 while 1, 2, 5 churns 4
    r = m.bind([('a', 1), ('a', 5), ('a', 2)])
    assert r['churn'] == {'a': 7} and r['calm'] == []
    r = m.bind([('a', 1), ('a', 2), ('a', 5)])
    assert r['churn'] == {'a': 4} and r['calm'] == ['a']
    # churn accumulates across every step, not just the last
    r = m.bind([('a', 5), ('a', 4), ('a', 5), ('a', 4)])
    assert r['churn'] == {'a': 3}
    # each antibody keeps its own running point
    r = m.bind([('a', 1), ('b', 9), ('a', 6), ('b', 1)])
    assert r == {'total': 4, 'churn': {'a': 5, 'b': 8}, 'calm': []}
    # boundary affinities
    r = m.bind([('a', 0), ('a', 10)])
    assert r['churn'] == {'a': 10} and r['calm'] == []
    # dynamic equal-string witness: equal antibodies share one run
    dyn = ''.join(['a', '1'])
    r = m.bind([(dyn, 2), (''.join(['a', '1']), 4)])
    assert r['churn'] == {'a1': 2} and r['calm'] == ['a1']
    # wide many-name sort pin, inserted in reverse order (20 antibodies)
    names = ['a%02d' % i for i in range(20)]
    r = m.bind([(n, 3) for n in reversed(names)])
    assert r['calm'] == sorted(names)
    assert r['churn'] == {n: 0 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.bind('nope')
    with pytest.raises(TypeError):
        m.bind(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.bind([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.bind([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.bind([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.bind([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.bind([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.bind([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.bind([('a', '1')])
    with pytest.raises(TypeError):
        m.bind([('a', LyingI())])
    with pytest.raises(TypeError):
        m.bind([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.bind([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.bind([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.bind([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.bind([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.bind({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.bind(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.bind([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.bind((('a', 1),)) == m.bind([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.bind([('a', 2), ['a', 5]])
    assert mixed == m.bind([['a', 2], ('a', 5)])
    # boundary acceptance pins
    assert m.bind([('abcdefgh', 1)])['churn'] == {'abcdefgh': 0}
    assert m.bind([('a', 1)] * 100)['total'] == 100
    assert m.bind([('a', 0)])['churn'] == {'a': 0}
    assert m.bind([('a', 10)])['churn'] == {'a': 0}
    # default-start pins: unknown antibody starts with churn 0
    r = m.bind([('zz', 2), ('zz', 4)])
    assert r['churn'] == {'zz': 2} and r['calm'] == ['zz']
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
    ('churn[antibody] += abs(affinity - last[antibody])',
     'churn[antibody] += affinity - last[antibody]'),
    ('churn[antibody] += abs(affinity - last[antibody])',
     'churn[antibody] = abs(affinity - last[antibody])'),
    ('abs(affinity - last[antibody])', 'abs(affinity - last[antibody]) + 1'),
    ('churn[antibody] = 0', 'churn[antibody] = 1'),
    ('if antibody not in last:', 'if antibody in last:'),
    ('last[antibody] = affinity', 'last[antibody] = affinity + 1'),
    ('total <= CALM', 'total < CALM'),
    ('CALM = 4', 'CALM = 3'),
    ('CALM = 4', 'CALM = 5'),
    ('calm = sorted(', 'calm = list('),
    ('MIN_AFFINITY = 0', 'MIN_AFFINITY = 1'),
    ('MAX_AFFINITY = 10', 'MAX_AFFINITY = 9'),
    ('not MIN_AFFINITY <= affinity <= MAX_AFFINITY',
     'not MIN_AFFINITY < affinity < MAX_AFFINITY'),
    ('antibody, affinity = row', 'affinity, antibody = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(churn)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(antibody) <= MAX_NAME',
     'not 1 <= len(antibody) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'churn': churn", "'churn': last"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.bind([(S('a'), 5)]), TypeError,
           'row 1: antibody must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.bind('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.bind(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.bind({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.bind([('a', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.bind([('a', 1), 'bad']), TypeError,
           'row 2: expected (antibody, affinity) tuple, got str')
    _exact(lambda: m.bind([('a', 1), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.bind([(1, 1)]), TypeError,
           'row 1: antibody must be str, got int')
    _exact(lambda: m.bind([(True, 1)]), TypeError,
           'row 1: antibody must be str, got bool')
    _exact(lambda: m.bind([('', 1)]), ValueError,
           'row 1: antibody must be 1-8 chars')
    _exact(lambda: m.bind([('abcdefghi', 1)]), ValueError,
           'row 1: antibody must be 1-8 chars')
    _exact(lambda: m.bind([('a', '1')]), TypeError,
           'row 1: affinity must be int, got str')
    _exact(lambda: m.bind([('a', True)]), TypeError,
           'row 1: affinity must be int, got bool')
    _exact(lambda: m.bind([('a', 11)]), ValueError,
           'row 1: affinity must be 0-10, got 11')
    _exact(lambda: m.bind([('a', -1)]), ValueError,
           'row 1: affinity must be 0-10, got -1')
    _exact(lambda: m.bind([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: antibody must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 975, Antibody Design' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: affinity bookkeeping only; no binding chemistry modeled'
    assert module.NOT_CLAIMED == (
        'does not model epitope recognition',
        'does not decay affinity between records',
        'does not compare antibodies against each other',
        'does not cap the churn during accumulation',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
