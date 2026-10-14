"""Mutation and oracle tests for extra_doc.drug_repurposing."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_978_drug_repurposing.py',
                        'src/sugarcode/extra_doc/drug_repurposing.py')

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
    # oracle seeded with row number 978
    assert m.rescue([]) == {'total': 0, 'plateaus': {}, 'anchored': []}
    # scores 3, 3 plateau at 2 and anchor
    r = m.rescue([('d', 3), ('d', 3)])
    assert r == {'total': 2, 'plateaus': {'d': 2}, 'anchored': ['d']}
    # 3, 3, 3 plateau at 3
    r = m.rescue([('d', 3), ('d', 3), ('d', 3)])
    assert r == {'total': 3, 'plateaus': {'d': 3}, 'anchored': ['d']}
    # 3, 4, 4 plateau at 2
    r = m.rescue([('d', 3), ('d', 4), ('d', 4)])
    assert r['plateaus'] == {'d': 2} and r['anchored'] == ['d']
    # a lone record plateaus at 1
    r = m.rescue([('d', 5)])
    assert r == {'total': 1, 'plateaus': {'d': 1}, 'anchored': []}
    # a broken run keeps its best, so 4, 4, 3, 3, 3 plateaus at 3
    r = m.rescue([('d', 4), ('d', 4), ('d', 3), ('d', 3), ('d', 3)])
    assert r['plateaus'] == {'d': 3} and r['anchored'] == ['d']
    # the longer run may come first: 3, 3, 3, 4, 4 plateaus at 3
    r = m.rescue([('d', 3), ('d', 3), ('d', 3), ('d', 4), ('d', 4)])
    assert r['plateaus'] == {'d': 3}
    # no repeats means no anchor
    r = m.rescue([('d', 1), ('d', 2), ('d', 3)])
    assert r['plateaus'] == {'d': 1} and r['anchored'] == []
    # another drug's record does not break the run
    r = m.rescue([('a', 3), ('b', 5), ('a', 3), ('b', 5)])
    assert r == {'total': 4, 'plateaus': {'a': 2, 'b': 2},
                 'anchored': ['a', 'b']}
    # boundary scores
    r = m.rescue([('d', 0), ('d', 0), ('d', 10), ('d', 10)])
    assert r['plateaus'] == {'d': 2} and r['anchored'] == ['d']
    # dynamic equal-string witness: equal drugs share one run
    dyn = ''.join(['d', '1'])
    r = m.rescue([(dyn, 4), (''.join(['d', '1']), 4)])
    assert r['plateaus'] == {'d1': 2} and r['anchored'] == ['d1']
    # wide many-name sort pin, inserted in reverse order (20 drugs)
    names = ['d%02d' % i for i in range(20)]
    r = m.rescue([(n, 3) for n in reversed(names)] + [(n, 3) for n in names])
    assert r['anchored'] == sorted(names)
    assert r['plateaus'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.rescue('nope')
    with pytest.raises(TypeError):
        m.rescue(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.rescue([('d', 1)] * 101)
    with pytest.raises(TypeError):
        m.rescue([('d', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.rescue([('d', 1), ('d',)])
    with pytest.raises(TypeError):
        m.rescue([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.rescue([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.rescue([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.rescue([('d', '1')])
    with pytest.raises(TypeError):
        m.rescue([('d', LyingI())])
    with pytest.raises(TypeError):
        m.rescue([('d', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.rescue([('d', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.rescue([('d', -1)])
    # first bad row pins, mixed failure types
    try:
        m.rescue([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.rescue([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.rescue({'d': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.rescue(ListSub([('d', 1)]))
    with pytest.raises(TypeError):
        m.rescue([ListSub(('d', 1))])
    # tuple rows accepted exactly like lists
    assert m.rescue((('d', 1),)) == m.rescue([('d', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.rescue([('d', 3), ['d', 3]])
    assert mixed == m.rescue([['d', 3], ('d', 3)])
    # boundary acceptance pins
    assert m.rescue([('abcdefgh', 1)])['plateaus'] == {'abcdefgh': 1}
    assert m.rescue([('d', 1)] * 100)['total'] == 100
    assert m.rescue([('d', 0)])['plateaus'] == {'d': 1}
    assert m.rescue([('d', 10)])['plateaus'] == {'d': 1}
    # default-start pins: unknown drug starts a run of 1
    r = m.rescue([('zz', 4), ('zz', 4)])
    assert r['plateaus'] == {'zz': 2} and r['anchored'] == ['zz']
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
    ('score == last[drug]', 'score != last[drug]'),
    ('score == last[drug]', 'score == last[drug] + 1'),
    ('runs[drug] += 1', 'runs[drug] = 1'),
    ('runs[drug] += 1', 'runs[drug] += 2'),
    ('plateaus[drug] = max(plateaus[drug], runs[drug])',
     'plateaus[drug] = runs[drug]'),
    ('runs[drug] = 1\n            plateaus[drug] = 1',
     'runs[drug] = 2\n            plateaus[drug] = 2'),
    ('runs[drug] = 1\n        last[drug] = score',
     'runs[drug] = 0\n        last[drug] = score'),
    ('if drug not in last:', 'if drug in last:'),
    ('last[drug] = score', 'last[drug] = score + 1'),
    ('plateau >= ANCHOR', 'plateau > ANCHOR'),
    ('ANCHOR = 2', 'ANCHOR = 1'),
    ('ANCHOR = 2', 'ANCHOR = 3'),
    ('anchored = sorted(', 'anchored = list('),
    ('MIN_SCORE = 0', 'MIN_SCORE = 1'),
    ('MAX_SCORE = 10', 'MAX_SCORE = 9'),
    ('not MIN_SCORE <= score <= MAX_SCORE',
     'not MIN_SCORE < score < MAX_SCORE'),
    ('drug, score = row', 'score, drug = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(plateaus)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(drug) <= MAX_NAME', 'not 1 <= len(drug) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'plateaus': plateaus", "'plateaus': runs"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.rescue([(S('d'), 5)]), TypeError,
           'row 1: drug must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.rescue('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.rescue(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.rescue({'d': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.rescue([('d', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.rescue([('d', 1), 'bad']), TypeError,
           'row 2: expected (drug, score) tuple, got str')
    _exact(lambda: m.rescue([('d', 1), ('d',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.rescue([(1, 1)]), TypeError,
           'row 1: drug must be str, got int')
    _exact(lambda: m.rescue([(True, 1)]), TypeError,
           'row 1: drug must be str, got bool')
    _exact(lambda: m.rescue([('', 1)]), ValueError,
           'row 1: drug must be 1-8 chars')
    _exact(lambda: m.rescue([('abcdefghi', 1)]), ValueError,
           'row 1: drug must be 1-8 chars')
    _exact(lambda: m.rescue([('d', '1')]), TypeError,
           'row 1: score must be int, got str')
    _exact(lambda: m.rescue([('d', True)]), TypeError,
           'row 1: score must be int, got bool')
    _exact(lambda: m.rescue([('d', 11)]), ValueError,
           'row 1: score must be 0-10, got 11')
    _exact(lambda: m.rescue([('d', -1)]), ValueError,
           'row 1: score must be 0-10, got -1')
    _exact(lambda: m.rescue([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: drug must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 978, Drug Repurposing' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: score bookkeeping only; no clinical evidence modeled'
    assert module.NOT_CLAIMED == (
        'does not model side effects',
        'does not weight scores by record order',
        'does not merge runs separated by other drugs',
        'does not compare drugs against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
