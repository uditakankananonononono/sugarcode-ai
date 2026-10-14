"""Mutation and oracle tests for extra_doc.evolutionary_strategies."""

import importlib.util
import signal
import sys
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_941_evolutionary_strategies.py',
                        'src/sugarcode/extra_doc/evolutionary_strategies.py')

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


class ListSub(list):
    pass


def _core(module):
    m = module
    # oracle seeded with row number 941
    assert m.mutate([]) == {'total': 0, 'scale': 0, 'shift': 0,
                            'survivors': [], 'eliminated': []}
    r = m.mutate([('a', 'scale'), ('a', 'shift'), ('a', 'scale')])
    assert r == {'total': 3, 'scale': 2, 'shift': 1,
                 'survivors': ['a'], 'eliminated': []}
    # three scales from 4: 2, 1, 0 -> eliminated
    r = m.mutate([('a', 'scale'), ('a', 'scale'), ('a', 'scale')])
    assert r['survivors'] == [] and r['eliminated'] == ['a']
    # two scales + one shift reaches exactly 1: still survives (strictly above 0)
    r = m.mutate([('a', 'scale'), ('a', 'scale'), ('a', 'shift')])
    assert r['survivors'] == ['a']
    # order dependence: shift first changes halving outcomes
    r = m.mutate([('a', 'shift'), ('a', 'scale'), ('a', 'scale'), ('a', 'scale')])
    assert r['eliminated'] == ['a']  # 5 -> 2 -> 1 -> 0
    r = m.mutate([('a', 'shift'), ('a', 'scale'), ('a', 'scale')])
    assert r['survivors'] == ['a']  # 5 -> 2 -> 1
    r = m.mutate([('a', 'scale'), ('a', 'scale'), ('a', 'shift'), ('a', 'scale')])
    assert r['survivors'] == ['a']  # 4 -> 2 -> 1 -> 2 -> 1; reversed fold ends at 0
    # multi-name sort pin (wide, deterministic)
    names = ['n%02d' % i for i in range(20)]
    rows = [(n, 'shift') for n in names]
    r = m.mutate(rows)
    assert r['survivors'] == sorted(names)
    assert r['total'] == 20
    # revival: reaching 0 then shifting back is a final-state survivor
    r = m.mutate([('a', 'scale'), ('a', 'scale'), ('a', 'scale'), ('a', 'shift')])
    assert r['survivors'] == ['a'] and r['eliminated'] == []  # 2, 1, 0, 1
    # mixed survivors/eliminated across names
    r = m.mutate([('b', 'shift'), ('a', 'scale'), ('a', 'scale'), ('a', 'scale')])
    assert r['survivors'] == ['b'] and r['eliminated'] == ['a']
    # dynamic equal-string witnesses: outcome must change under is-misread
    dyn = ''.join(['sc', 'ale'])
    r = m.mutate([('a', dyn), ('a', dyn), ('a', dyn)])
    assert r['eliminated'] == ['a'] and r['scale'] == 3
    dyn2 = ''.join(['sh', 'ift'])
    r = m.mutate([('a', dyn2), ('a', dyn2), ('a', dyn2), ('a', dyn2), ('a', dyn2)])
    assert r['survivors'] == ['a'] and r['shift'] == 5
    # shift-magnitude pin: +1 vs +2 diverges across halvings
    r = m.mutate([('a', 'shift'), ('a', 'shift'),
                  ('a', 'scale'), ('a', 'scale'), ('a', 'scale')])
    assert r['eliminated'] == ['a']  # 6 -> 3 -> 1 -> 0; +2 would reach 8 -> 4 -> 2 -> 1
    # start-score pin: 4 vs 5 diverges after three shifts then three scales
    r = m.mutate([('a', 'shift'), ('a', 'shift'), ('a', 'shift'),
                  ('a', 'scale'), ('a', 'scale'), ('a', 'scale')])
    assert r['eliminated'] == ['a']  # 7 -> 3 -> 1 -> 0; start 5 reaches 8 -> 4 -> 2 -> 1
    # mixed dynamic: first pin outcome flips if 'scale' misread as shift
    r = m.mutate([('a', dyn), ('a', dyn)])
    assert r == {'total': 2, 'scale': 2, 'shift': 0,
                 'survivors': ['a'], 'eliminated': []}  # 4->2->1 survives
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.mutate('nope')
    with pytest.raises(TypeError):
        m.mutate(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.mutate([('a', 'shift')] * 101)
    with pytest.raises(TypeError):
        m.mutate([('a', 'shift'), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.mutate([('a', 'shift'), ('a',)])
    with pytest.raises(TypeError):
        m.mutate([(1, 'shift')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.mutate([('', 'shift')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.mutate([('abcdefghi', 'shift')])
    with pytest.raises(TypeError):
        m.mutate([('a', 1)])
    with pytest.raises(ValueError, match="one of"):
        m.mutate([('a', 'jump')])
    # first bad row pins, mixed failure types
    try:
        m.mutate([('ok', 'shift'), ('ok', 'scale'), (7, 'shift')])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.mutate([('ok', 'shift'), ('ok', 'nope')])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.mutate({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.mutate(ListSub([('a', 'shift')]))
    with pytest.raises(TypeError):
        m.mutate([ListSub(('a', 'shift'))])
    # tuple rows accepted exactly like lists
    assert m.mutate((('a', 'shift'),)) == m.mutate([('a', 'shift')])
    # boundary acceptance pins
    assert m.mutate([('abcdefgh', 'shift')])['survivors'] == ['abcdefgh']
    assert m.mutate([('a', 'shift')] * 100)['total'] == 100
    # pre-seed pins: unknown strategy must start at 4
    r = m.mutate([('zz', 'shift')])
    assert r['survivors'] == ['zz']  # 4+1=5 survives either way...
    r = m.mutate([('zz', 'scale'), ('zz', 'scale'), ('zz', 'scale')])
    assert r['eliminated'] == ['zz']  # start 4 -> 2 -> 1 -> 0; start 0 would stay 0 (equiv); start 1 -> 0 after 2
    r = m.mutate([('zz', 'scale')])
    assert r['survivors'] == ['zz']  # 4//2=2 > 0; a start of 1 gives 0 -> eliminated
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
    ("if operator == 'scale':", "if operator is 'scale':"),
    ("if operator == 'scale':", "if operator != 'scale':"),
    ("level // 2 if operator == 'scale' else level + 1",
     "level + 1 if operator == 'scale' else level // 2"),
    ("level // 2 if operator == 'scale' else level + 1",
     "level // 2 if operator is 'scale' else level + 1"),
    ('level // 2', 'level // 3'),
    ('level // 2', 'level // 2 + 1'),
    ('level + 1', 'level + 2'),
    ('level + 1', 'level - 1'),
    ('scores.get(strategy, START_SCORE)', 'scores.get(strategy, 0)'),
    ('scores.get(strategy, START_SCORE)', 'scores.get(strategy, 1)'),
    ('START_SCORE = 4', 'START_SCORE = 5'),
    ('if value > 0', 'if value >= 0'),
    ('if value > 0', 'if value < 0'),
    ('sorted(name for name, value in scores.items() if value > 0)',
     'sorted(name for name, value in scores.items() if value >= 0)'),
    ('sorted(name for name, value in scores.items() if value <= 0)',
     'sorted(name for name, value in scores.items() if value < 0)'),
    ('scale += 1', 'scale += 2'),
    ('shift += 1', 'shift += 2'),
    ("'total': len(rows)", "'total': len(scores)"),
    ('strategy, operator = row', 'operator, strategy = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("OPERATORS = ('scale', 'shift')", "OPERATORS = ('scale', 'shift', 'jump')"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(strategy) <= MAX_NAME', 'not 1 <= len(strategy) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 941, Evolutionary Strategies' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
