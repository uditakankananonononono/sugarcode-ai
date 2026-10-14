"""Mutation and oracle tests for extra_doc.directed_evolution."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_973_directed_evolution.py',
                        'src/sugarcode/extra_doc/directed_evolution.py')

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
    # oracle seeded with row number 973
    assert m.evolve([]) == {'total': 0, 'gains': {}, 'risen': []}
    # fitness 2 then 5 gains 3 and rises
    r = m.evolve([('l', 2), ('l', 5)])
    assert r == {'total': 2, 'gains': {'l': 3}, 'risen': ['l']}
    # 5 then 2 loses 3 and stays down
    r = m.evolve([('l', 5), ('l', 2)])
    assert r == {'total': 2, 'gains': {'l': -3}, 'risen': []}
    # a lone record gains nothing
    r = m.evolve([('l', 7)])
    assert r == {'total': 1, 'gains': {'l': 0}, 'risen': []}
    # a gain of exactly 3 still counts
    r = m.evolve([('l', 4), ('l', 7)])
    assert r['gains'] == {'l': 3} and r['risen'] == ['l']
    # a gain of 2 falls short
    r = m.evolve([('l', 4), ('l', 6)])
    assert r['gains'] == {'l': 2} and r['risen'] == []
    # only the first and last records set the gain, so 2, 9, 5 nets 3
    r = m.evolve([('l', 2), ('l', 9), ('l', 5)])
    assert r['gains'] == {'l': 3} and r['risen'] == ['l']
    # the same middle record nets -3 in reverse
    r = m.evolve([('l', 5), ('l', 9), ('l', 2)])
    assert r['gains'] == {'l': -3} and r['risen'] == []
    # each lineage keeps its own first and last
    r = m.evolve([('a', 2), ('b', 8), ('a', 5), ('b', 1)])
    assert r == {'total': 4, 'gains': {'a': 3, 'b': -7}, 'risen': ['a']}
    # boundary fitnesses
    r = m.evolve([('l', 0), ('l', 10)])
    assert r['gains'] == {'l': 10} and r['risen'] == ['l']
    # dynamic equal-string witness: equal lineages share one gain
    dyn = ''.join(['l', '1'])
    r = m.evolve([(dyn, 1), (''.join(['l', '1']), 4)])
    assert r['gains'] == {'l1': 3} and r['risen'] == ['l1']
    # wide many-name sort pin, inserted in reverse order (20 lineages)
    names = ['l%02d' % i for i in range(20)]
    r = m.evolve([(n, 4) for n in reversed(names)] + [(n, 7) for n in names])
    assert r['risen'] == sorted(names)
    assert r['gains'] == {n: 3 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.evolve('nope')
    with pytest.raises(TypeError):
        m.evolve(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.evolve([('l', 1)] * 101)
    with pytest.raises(TypeError):
        m.evolve([('l', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.evolve([('l', 1), ('l',)])
    with pytest.raises(TypeError):
        m.evolve([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.evolve([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.evolve([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.evolve([('l', '1')])
    with pytest.raises(TypeError):
        m.evolve([('l', LyingI())])
    with pytest.raises(TypeError):
        m.evolve([('l', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.evolve([('l', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.evolve([('l', -1)])
    # first bad row pins, mixed failure types
    try:
        m.evolve([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.evolve([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.evolve({'l': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.evolve(ListSub([('l', 1)]))
    with pytest.raises(TypeError):
        m.evolve([ListSub(('l', 1))])
    # tuple rows accepted exactly like lists
    assert m.evolve((('l', 1),)) == m.evolve([('l', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.evolve([('l', 2), ['l', 5]])
    assert mixed == m.evolve([['l', 2], ('l', 5)])
    # boundary acceptance pins
    assert m.evolve([('abcdefgh', 1)])['gains'] == {'abcdefgh': 0}
    assert m.evolve([('l', 1)] * 100)['total'] == 100
    assert m.evolve([('l', 0), ('l', 3)])['gains'] == {'l': 3}
    assert m.evolve([('l', 10), ('l', 7)])['gains'] == {'l': -3}
    # default-start pins: unknown lineage seeds both ends at 0 net
    r = m.evolve([('zz', 4), ('zz', 7)])
    assert r['gains'] == {'zz': 3} and r['risen'] == ['zz']
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
    ('lasts[lineage] - firsts[lineage]',
     'firsts[lineage] - lasts[lineage]'),
    ('if lineage not in firsts:', 'if lineage in firsts:'),
    ('firsts[lineage] = fitness', 'firsts[lineage] = 0'),
    ('lasts[lineage] = fitness', 'lasts[lineage] = 0'),
    ('gain >= RISE', 'gain > RISE'),
    ('RISE = 3', 'RISE = 2'),
    ('RISE = 3', 'RISE = 4'),
    ('risen = sorted(', 'risen = list('),
    ('MIN_FITNESS = 0', 'MIN_FITNESS = 1'),
    ('MAX_FITNESS = 10', 'MAX_FITNESS = 9'),
    ('not MIN_FITNESS <= fitness <= MAX_FITNESS',
     'not MIN_FITNESS < fitness < MAX_FITNESS'),
    ('lineage, fitness = row', 'fitness, lineage = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(firsts)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(lineage) <= MAX_NAME',
     'not 1 <= len(lineage) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'gains': gains", "'gains': firsts"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.evolve([(S('l'), 5)]), TypeError,
           'row 1: lineage must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.evolve('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.evolve(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.evolve({'l': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.evolve([('l', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.evolve([('l', 1), 'bad']), TypeError,
           'row 2: expected (lineage, fitness) tuple, got str')
    _exact(lambda: m.evolve([('l', 1), ('l',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.evolve([(1, 1)]), TypeError,
           'row 1: lineage must be str, got int')
    _exact(lambda: m.evolve([(True, 1)]), TypeError,
           'row 1: lineage must be str, got bool')
    _exact(lambda: m.evolve([('', 1)]), ValueError,
           'row 1: lineage must be 1-8 chars')
    _exact(lambda: m.evolve([('abcdefghi', 1)]), ValueError,
           'row 1: lineage must be 1-8 chars')
    _exact(lambda: m.evolve([('l', '1')]), TypeError,
           'row 1: fitness must be int, got str')
    _exact(lambda: m.evolve([('l', True)]), TypeError,
           'row 1: fitness must be int, got bool')
    _exact(lambda: m.evolve([('l', 11)]), ValueError,
           'row 1: fitness must be 0-10, got 11')
    _exact(lambda: m.evolve([('l', -1)]), ValueError,
           'row 1: fitness must be 0-10, got -1')
    _exact(lambda: m.evolve([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: lineage must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 973, Directed Evolution' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: fitness bookkeeping only; no selection dynamics modeled'
    assert module.NOT_CLAIMED == (
        'does not model mutation rates',
        'does not weight fitness by generation',
        'does not read the middle records',
        'does not compare lineages against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
