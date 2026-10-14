"""Mutation and oracle tests for extra_doc.chemogenetics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_1000_chemogenetics.py',
                        'src/sugarcode/extra_doc/chemogenetics.py')

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
    # oracle seeded with row number 1000
    assert m.bind([]) == {'total': 0, 'bonds': {}, 'chained': []}
    # doses 1, 1, 2, 3, 5 chain 3 times
    r = m.bind([('r', 1), ('r', 1), ('r', 2), ('r', 3), ('r', 5)])
    assert r == {'total': 5, 'bonds': {'r': 3}, 'chained': ['r']}
    # 1, 2, 3 chain once
    r = m.bind([('r', 1), ('r', 2), ('r', 3)])
    assert r == {'total': 3, 'bonds': {'r': 1}, 'chained': []}
    # 1, 2, 3, 5 chain twice and read chained: boundary
    r = m.bind([('r', 1), ('r', 2), ('r', 3), ('r', 5)])
    assert r == {'total': 4, 'bonds': {'r': 2}, 'chained': ['r']}
    # 2, 3, 5 chain once
    r = m.bind([('r', 2), ('r', 3), ('r', 5)])
    assert r == {'total': 3, 'bonds': {'r': 1}, 'chained': []}
    # 1, 2, 4 chain 0
    r = m.bind([('r', 1), ('r', 2), ('r', 4)])
    assert r == {'total': 3, 'bonds': {'r': 0}, 'chained': []}
    # 0, 0, 0 chain once
    r = m.bind([('r', 0), ('r', 0), ('r', 0)])
    assert r == {'total': 3, 'bonds': {'r': 1}, 'chained': []}
    # 3, 0, 3 chain once: 0 is a valid addend
    r = m.bind([('r', 3), ('r', 0), ('r', 3)])
    assert r == {'total': 3, 'bonds': {'r': 1}, 'chained': []}
    # 5, 5, 10 chain once
    r = m.bind([('r', 5), ('r', 5), ('r', 10)])
    assert r == {'total': 3, 'bonds': {'r': 1}, 'chained': []}
    # 0, 0, 0, 0 chain twice and read chained
    r = m.bind([('r', 0), ('r', 0), ('r', 0), ('r', 0)])
    assert r == {'total': 4, 'bonds': {'r': 2}, 'chained': ['r']}
    # a lone dose chains 0
    r = m.bind([('r', 7)])
    assert r == {'total': 1, 'bonds': {'r': 0}, 'chained': []}
    # each receptor keeps its own bonds
    r = m.bind([('a', 1), ('b', 2), ('a', 1), ('a', 2)])
    assert r == {'total': 4, 'bonds': {'a': 1, 'b': 0},
                 'chained': []}
    # dynamic equal-string witness: equal receptors share one count
    dyn = ''.join(['r', '1'])
    r = m.bind([(dyn, 1), (''.join(['r', '1']), 2),
                (''.join(['r', '1']), 3), (dyn, 5)])
    assert r['bonds'] == {'r1': 2} and r['chained'] == ['r1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['r%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 2), (n, 3), (n, 5)]
    r = m.bind(rows)
    assert r['chained'] == sorted(names)
    assert r['bonds'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.bind('nope')
    with pytest.raises(TypeError):
        m.bind(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.bind([('r', 1)] * 101)
    with pytest.raises(TypeError):
        m.bind([('r', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.bind([('r', 1), ('r',)])
    with pytest.raises(TypeError):
        m.bind([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.bind([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.bind([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.bind([('r', '1')])
    with pytest.raises(TypeError):
        m.bind([('r', LyingI())])
    with pytest.raises(TypeError):
        m.bind([('r', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.bind([('r', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.bind([('r', -1)])
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
        m.bind({'r': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.bind(ListSub([('r', 1)]))
    with pytest.raises(TypeError):
        m.bind([ListSub(('r', 1))])
    # tuple rows accepted exactly like lists
    assert m.bind((('r', 1),)) == m.bind([('r', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.bind([('r', 1), ['r', 2], ('r', 3)])
    assert mixed == m.bind([['r', 1], ('r', 2), ['r', 3]])
    # boundary acceptance pins
    assert m.bind([('abcdefgh', 1)])['bonds'] == {'abcdefgh': 0}
    assert m.bind([('r', 1)] * 100)['total'] == 100
    assert m.bind([('r', 0)])['bonds'] == {'r': 0}
    assert m.bind([('r', 10)])['bonds'] == {'r': 0}
    # default-start pins: unknown receptor starts with no bonds
    r = m.bind([('zz', 1), ('zz', 2), ('zz', 3)])
    assert r['bonds'] == {'zz': 1} and r['chained'] == []
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
    ('vals[i] + vals[i + 1] == vals[i + 2]',
     'vals[i] + vals[i + 1] != vals[i + 2]'),
    ('vals[i] + vals[i + 1] == vals[i + 2]',
     'vals[i] - vals[i + 1] == vals[i + 2]'),
    ('vals[i] + vals[i + 1] == vals[i + 2]',
     'vals[i] + vals[i + 2] == vals[i + 1]'),
    ('vals[i] + vals[i + 1] == vals[i + 2]',
     'vals[i] * vals[i + 1] == vals[i + 2]'),
    ('range(len(vals) - 2)', 'range(len(vals))'),
    ('range(len(vals) - 2)', 'range(1, len(vals) - 2)'),
    ('range(len(vals) - 2)', 'range(len(vals) - 1)'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('count >= CHAINED', 'count > CHAINED'),
    ('count >= CHAINED', 'count >= CHAINED + 1'),
    ('CHAINED = 2', 'CHAINED = 1'),
    ('CHAINED = 2', 'CHAINED = 3'),
    ('chained = sorted(', 'chained = list('),
    ('values.setdefault(receptor, []).append(dose)',
     'values.setdefault(receptor, [1]).append(dose)'),
    ('values: dict = {}', "values: dict = {'zz': [1, 2, 3]}"),
    ('bonds = {}', "bonds = {'zz': 5}"),
    ('receptor, dose = row', 'dose, receptor = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(bonds)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(receptor) <= MAX_NAME',
     'not 1 <= len(receptor) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_DOSE = 0', 'MIN_DOSE = 1'),
    ('MAX_DOSE = 10', 'MAX_DOSE = 9'),
    ('not MIN_DOSE <= dose <= MAX_DOSE',
     'not MIN_DOSE < dose < MAX_DOSE'),
    ("'bonds': bonds", "'bonds': chained"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.bind([(S('r'), 5)]), TypeError,
           'row 1: receptor must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.bind('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.bind(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.bind({'r': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.bind([('r', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.bind([('r', 1), 'bad']), TypeError,
           'row 2: expected (receptor, dose) tuple, got str')
    _exact(lambda: m.bind([('r', 1), ('r',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.bind([(1, 1)]), TypeError,
           'row 1: receptor must be str, got int')
    _exact(lambda: m.bind([(True, 1)]), TypeError,
           'row 1: receptor must be str, got bool')
    _exact(lambda: m.bind([('', 1)]), ValueError,
           'row 1: receptor must be 1-8 chars')
    _exact(lambda: m.bind([('abcdefghi', 1)]), ValueError,
           'row 1: receptor must be 1-8 chars')
    _exact(lambda: m.bind([('r', '1')]), TypeError,
           'row 1: dose must be int, got str')
    _exact(lambda: m.bind([('r', True)]), TypeError,
           'row 1: dose must be int, got bool')
    _exact(lambda: m.bind([('r', 11)]), ValueError,
           'row 1: dose must be 0-10, got 11')
    _exact(lambda: m.bind([('r', -1)]), ValueError,
           'row 1: dose must be 0-10, got -1')
    _exact(lambda: m.bind([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: receptor must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 1000, Chemogenetics' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: dose bookkeeping only; no DREADD signaling modeled'
    assert module.NOT_CLAIMED == (
        'does not model ligand affinity',
        'does not count non-consecutive dose triples',
        'does not cap the sum at the dose range',
        'does not compare receptors against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
