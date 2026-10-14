"""Mutation and oracle tests for extra_doc.targeted_drug_delivery."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_989_targeted_drug_delivery.py',
                        'src/sugarcode/extra_doc/targeted_drug_delivery.py')

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
    # oracle seeded with row number 989
    assert m.deliver([]) == {'total': 0, 'courses': {}, 'ready': []}
    # doses 3, 3, 3 pool to 9 and buy 2 courses, so the target is ready
    r = m.deliver([('t', 3), ('t', 3), ('t', 3)])
    assert r == {'total': 3, 'courses': {'t': 2}, 'ready': ['t']}
    # 4 buys 1
    r = m.deliver([('t', 4)])
    assert r == {'total': 1, 'courses': {'t': 1}, 'ready': []}
    # 4, 4 buy 2 and ready: boundary on the ready side
    r = m.deliver([('t', 4), ('t', 4)])
    assert r == {'total': 2, 'courses': {'t': 2}, 'ready': ['t']}
    # 7 buys 1, 8 buys 2: quotient boundary on both sides
    r = m.deliver([('t', 7)])
    assert r == {'total': 1, 'courses': {'t': 1}, 'ready': []}
    r = m.deliver([('t', 8)])
    assert r == {'total': 1, 'courses': {'t': 2}, 'ready': ['t']}
    # 3 alone buys 0
    r = m.deliver([('t', 3)])
    assert r == {'total': 1, 'courses': {'t': 0}, 'ready': []}
    # 3, 4 pool to 7 and buy 1; leftovers never round up
    r = m.deliver([('t', 3), ('t', 4)])
    assert r == {'total': 2, 'courses': {'t': 1}, 'ready': []}
    # a zero dose buys 0
    r = m.deliver([('t', 0), ('t', 3)])
    assert r == {'total': 2, 'courses': {'t': 0}, 'ready': []}
    # boundary doses: 10, 10 pool to 20 and buy 5 courses
    r = m.deliver([('t', 10), ('t', 10)])
    assert r == {'total': 2, 'courses': {'t': 5}, 'ready': ['t']}
    # each target keeps its own pool
    r = m.deliver([('b', 4), ('a', 4), ('b', 4), ('a', 4)])
    assert r == {'total': 4, 'courses': {'b': 2, 'a': 2},
                 'ready': ['a', 'b']}
    # dynamic equal-string witness: equal targets share one pool
    dyn = ''.join(['t', '1'])
    r = m.deliver([(dyn, 3), (''.join(['t', '1']), 3),
                   (''.join(['t', '1']), 3)])
    assert r['courses'] == {'t1': 2} and r['ready'] == ['t1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['t%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 4), (n, 4)]
    r = m.deliver(rows)
    assert r['ready'] == sorted(names)
    assert r['courses'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.deliver('nope')
    with pytest.raises(TypeError):
        m.deliver(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.deliver([('t', 1)] * 101)
    with pytest.raises(TypeError):
        m.deliver([('t', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.deliver([('t', 1), ('t',)])
    with pytest.raises(TypeError):
        m.deliver([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.deliver([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.deliver([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.deliver([('t', '1')])
    with pytest.raises(TypeError):
        m.deliver([('t', LyingI())])
    with pytest.raises(TypeError):
        m.deliver([('t', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.deliver([('t', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.deliver([('t', -1)])
    # first bad row pins, mixed failure types
    try:
        m.deliver([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.deliver([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.deliver({'t': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.deliver(ListSub([('t', 1)]))
    with pytest.raises(TypeError):
        m.deliver([ListSub(('t', 1))])
    # tuple rows accepted exactly like lists
    assert m.deliver((('t', 1),)) == m.deliver([('t', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.deliver([('t', 3), ['t', 3], ('t', 3)])
    assert mixed == m.deliver([['t', 3], ('t', 3), ['t', 3]])
    # boundary acceptance pins
    assert m.deliver([('abcdefgh', 1)])['courses'] == {'abcdefgh': 0}
    assert m.deliver([('t', 1)] * 100)['total'] == 100
    assert m.deliver([('t', 0)])['courses'] == {'t': 0}
    assert m.deliver([('t', 10)])['courses'] == {'t': 2}
    # default-start pins: unknown target starts with no pool
    r = m.deliver([('zz', 4)])
    assert r['courses'] == {'zz': 1} and r['ready'] == []
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
    ('totals[target] += dose', 'totals[target] = dose'),
    ('totals[target] += dose', 'totals[target] += 1'),
    ('totals[target] += dose', 'totals[target] += dose * 2'),
    ('totals.setdefault(target, 0)', 'totals.setdefault(target, 1)'),
    ('tot // COURSE', 'tot / COURSE'),
    ('tot // COURSE', 'tot % COURSE'),
    ('tot // COURSE', 'tot // COURSE + 1'),
    ('COURSE = 4', 'COURSE = 3'),
    ('COURSE = 4', 'COURSE = 5'),
    ('c >= READY', 'c > READY'),
    ('c >= READY', 'c >= READY + 1'),
    ('READY = 2', 'READY = 1'),
    ('READY = 2', 'READY = 3'),
    ('ready = sorted(', 'ready = list('),
    ('totals: dict = {}', "totals: dict = {'zz': 8}"),
    ('target, dose = row', 'dose, target = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(courses)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(target) <= MAX_NAME',
     'not 1 <= len(target) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_DOSE = 0', 'MIN_DOSE = 1'),
    ('MAX_DOSE = 10', 'MAX_DOSE = 9'),
    ('not MIN_DOSE <= dose <= MAX_DOSE',
     'not MIN_DOSE < dose < MAX_DOSE'),
    ("'courses': courses", "'courses': ready"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.deliver([(S('t'), 5)]), TypeError,
           'row 1: target must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.deliver('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.deliver(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.deliver({'t': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.deliver([('t', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.deliver([('t', 1), 'bad']), TypeError,
           'row 2: expected (target, dose) tuple, got str')
    _exact(lambda: m.deliver([('t', 1), ('t',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.deliver([(1, 1)]), TypeError,
           'row 1: target must be str, got int')
    _exact(lambda: m.deliver([(True, 1)]), TypeError,
           'row 1: target must be str, got bool')
    _exact(lambda: m.deliver([('', 1)]), ValueError,
           'row 1: target must be 1-8 chars')
    _exact(lambda: m.deliver([('abcdefghi', 1)]), ValueError,
           'row 1: target must be 1-8 chars')
    _exact(lambda: m.deliver([('t', '1')]), TypeError,
           'row 1: dose must be int, got str')
    _exact(lambda: m.deliver([('t', True)]), TypeError,
           'row 1: dose must be int, got bool')
    _exact(lambda: m.deliver([('t', 11)]), ValueError,
           'row 1: dose must be 0-10, got 11')
    _exact(lambda: m.deliver([('t', -1)]), ValueError,
           'row 1: dose must be 0-10, got -1')
    _exact(lambda: m.deliver([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: target must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 989, Targeted Drug Delivery' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: dose bookkeeping only; no pharmacokinetics modeled'
    assert module.NOT_CLAIMED == (
        'does not model dose timing or intervals',
        'does not weight doses by record order',
        'does not round leftover units up to a course',
        'does not compare targets against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
