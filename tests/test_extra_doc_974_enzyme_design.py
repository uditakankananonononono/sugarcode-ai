"""Mutation and oracle tests for extra_doc.enzyme_design."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_974_enzyme_design.py',
                        'src/sugarcode/extra_doc/enzyme_design.py')

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
    # oracle seeded with row number 974
    assert m.catalyze([]) == {'total': 0, 'runners': {}, 'deep': []}
    # rates 9, 5 give a runner of 5
    r = m.catalyze([('e', 9), ('e', 5)])
    assert r == {'total': 2, 'runners': {'e': 5}, 'deep': []}
    # rates 5, 9, 7 give a runner of 7
    r = m.catalyze([('e', 5), ('e', 9), ('e', 7)])
    assert r == {'total': 3, 'runners': {'e': 7}, 'deep': ['e']}
    # a lone rate fields itself as its own runner
    r = m.catalyze([('e', 3)])
    assert r == {'total': 1, 'runners': {'e': 3}, 'deep': []}
    # two equal rates 9, 9 give a runner of 9
    r = m.catalyze([('e', 9), ('e', 9)])
    assert r['runners'] == {'e': 9} and r['deep'] == ['e']
    # a runner of exactly 6 still counts deep
    r = m.catalyze([('e', 8), ('e', 6)])
    assert r['runners'] == {'e': 6} and r['deep'] == ['e']
    # a runner of 5 falls short
    r = m.catalyze([('e', 8), ('e', 5)])
    assert r['runners'] == {'e': 5} and r['deep'] == []
    # the runner is the second best, not the second record
    r = m.catalyze([('e', 5), ('e', 7), ('e', 9)])
    assert r['runners'] == {'e': 7}
    # the best may repeat below the top
    r = m.catalyze([('e', 9), ('e', 5), ('e', 8)])
    assert r['runners'] == {'e': 8}
    # each enzyme keeps its own record list
    r = m.catalyze([('a', 8), ('b', 3), ('a', 7), ('b', 2)])
    assert r == {'total': 4, 'runners': {'a': 7, 'b': 2}, 'deep': ['a']}
    # boundary rates
    r = m.catalyze([('e', 10), ('e', 0)])
    assert r['runners'] == {'e': 0} and r['deep'] == []
    # dynamic equal-string witness: equal enzymes share one list
    dyn = ''.join(['e', '1'])
    r = m.catalyze([(dyn, 8), (''.join(['e', '1']), 7)])
    assert r['runners'] == {'e1': 7} and r['deep'] == ['e1']
    # wide many-name sort pin, inserted in reverse order (20 enzymes)
    names = ['e%02d' % i for i in range(20)]
    r = m.catalyze([(n, 7) for n in reversed(names)] + [(n, 8) for n in names])
    assert r['deep'] == sorted(names)
    assert r['runners'] == {n: 7 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.catalyze('nope')
    with pytest.raises(TypeError):
        m.catalyze(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.catalyze([('e', 1)] * 101)
    with pytest.raises(TypeError):
        m.catalyze([('e', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.catalyze([('e', 1), ('e',)])
    with pytest.raises(TypeError):
        m.catalyze([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.catalyze([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.catalyze([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.catalyze([('e', '1')])
    with pytest.raises(TypeError):
        m.catalyze([('e', LyingI())])
    with pytest.raises(TypeError):
        m.catalyze([('e', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.catalyze([('e', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.catalyze([('e', -1)])
    # first bad row pins, mixed failure types
    try:
        m.catalyze([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.catalyze([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.catalyze({'e': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.catalyze(ListSub([('e', 1)]))
    with pytest.raises(TypeError):
        m.catalyze([ListSub(('e', 1))])
    # tuple rows accepted exactly like lists
    assert m.catalyze((('e', 1),)) == m.catalyze([('e', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.catalyze([('e', 9), ['e', 5]])
    assert mixed == m.catalyze([['e', 9], ('e', 5)])
    # boundary acceptance pins
    assert m.catalyze([('abcdefgh', 1)])['runners'] == {'abcdefgh': 1}
    assert m.catalyze([('e', 1)] * 100)['total'] == 100
    assert m.catalyze([('e', 0)])['runners'] == {'e': 0}
    assert m.catalyze([('e', 10)])['runners'] == {'e': 10}
    # default-start pins: unknown enzyme starts from an empty list
    r = m.catalyze([('zz', 9), ('zz', 7)])
    assert r['runners'] == {'zz': 7} and r['deep'] == ['zz']
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
    ('ordered = sorted(values, reverse=True)', 'ordered = sorted(values)'),
    ('ordered[1] if len(ordered) > 1 else ordered[0]',
     'ordered[0] if len(ordered) > 1 else ordered[1]'),
    ('ordered[1] if len(ordered) > 1 else ordered[0]',
     'ordered[1] if len(ordered) > 2 else ordered[0]'),
    ('rates[enzyme].append(rate)', 'rates[enzyme].append(rate + 1)'),
    ('rates[enzyme] = []', 'rates[enzyme] = [6]'),
    ('if enzyme not in rates:', 'if enzyme in rates:'),
    ('runner >= DEPTH', 'runner > DEPTH'),
    ('DEPTH = 6', 'DEPTH = 5'),
    ('DEPTH = 6', 'DEPTH = 7'),
    ('deep = sorted(', 'deep = list('),
    ('MIN_RATE = 0', 'MIN_RATE = 1'),
    ('MAX_RATE = 10', 'MAX_RATE = 9'),
    ('not MIN_RATE <= rate <= MAX_RATE',
     'not MIN_RATE < rate < MAX_RATE'),
    ('enzyme, rate = row', 'rate, enzyme = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(rates)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(enzyme) <= MAX_NAME',
     'not 1 <= len(enzyme) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'runners': runners", "'runners': rates"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.catalyze([(S('e'), 5)]), TypeError,
           'row 1: enzyme must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.catalyze('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.catalyze(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.catalyze({'e': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.catalyze([('e', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.catalyze([('e', 1), 'bad']), TypeError,
           'row 2: expected (enzyme, rate) tuple, got str')
    _exact(lambda: m.catalyze([('e', 1), ('e',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.catalyze([(1, 1)]), TypeError,
           'row 1: enzyme must be str, got int')
    _exact(lambda: m.catalyze([(True, 1)]), TypeError,
           'row 1: enzyme must be str, got bool')
    _exact(lambda: m.catalyze([('', 1)]), ValueError,
           'row 1: enzyme must be 1-8 chars')
    _exact(lambda: m.catalyze([('abcdefghi', 1)]), ValueError,
           'row 1: enzyme must be 1-8 chars')
    _exact(lambda: m.catalyze([('e', '1')]), TypeError,
           'row 1: rate must be int, got str')
    _exact(lambda: m.catalyze([('e', True)]), TypeError,
           'row 1: rate must be int, got bool')
    _exact(lambda: m.catalyze([('e', 11)]), ValueError,
           'row 1: rate must be 0-10, got 11')
    _exact(lambda: m.catalyze([('e', -1)]), ValueError,
           'row 1: rate must be 0-10, got -1')
    _exact(lambda: m.catalyze([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: enzyme must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 974, Enzyme Design' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: rate bookkeeping only; no catalytic mechanism modeled'
    assert module.NOT_CLAIMED == (
        'does not model substrate affinity',
        'does not weight rates by record order',
        'does not average the rates',
        'does not compare enzymes against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
