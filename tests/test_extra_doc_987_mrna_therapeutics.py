"""Mutation and oracle tests for extra_doc.mrna_therapeutics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_987_mrna_therapeutics.py',
                        'src/sugarcode/extra_doc/mrna_therapeutics.py')

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
    # oracle seeded with row number 987
    assert m.translate([]) == {'total': 0, 'spreads': {}, 'tight': []}
    # expressions 1, 2, 4 spread to 1 + 3 + 2 = 6
    r = m.translate([('s', 1), ('s', 2), ('s', 4)])
    assert r == {'total': 3, 'spreads': {'s': 6}, 'tight': []}
    # 3, 3 spread to 0 and stay tight
    r = m.translate([('s', 3), ('s', 3)])
    assert r == {'total': 2, 'spreads': {'s': 0}, 'tight': ['s']}
    # 1, 2, 3 spread to 4 and stay tight: boundary on the tight side
    r = m.translate([('s', 1), ('s', 2), ('s', 3)])
    assert r == {'total': 3, 'spreads': {'s': 4}, 'tight': ['s']}
    # 0, 2, 4 spread to 8
    r = m.translate([('s', 0), ('s', 2), ('s', 4)])
    assert r == {'total': 3, 'spreads': {'s': 8}, 'tight': []}
    # 0, 5 spread to 5: boundary on the loose side
    r = m.translate([('s', 0), ('s', 5)])
    assert r == {'total': 2, 'spreads': {'s': 5}, 'tight': []}
    # a lone expression spreads to 0
    r = m.translate([('s', 7)])
    assert r == {'total': 1, 'spreads': {'s': 0}, 'tight': ['s']}
    # record order does not change a spread
    r = m.translate([('s', 4), ('s', 1), ('s', 2)])
    assert r['spreads'] == {'s': 6}
    # each sequence keeps its own spread
    r = m.translate([('a', 1), ('b', 9), ('a', 2), ('a', 4)])
    assert r == {'total': 4, 'spreads': {'a': 6, 'b': 0},
                 'tight': ['b']}
    # boundary expressions
    r = m.translate([('s', 0), ('s', 10)])
    assert r['spreads'] == {'s': 10} and r['tight'] == []
    r = m.translate([('s', 10), ('s', 10)])
    assert r['spreads'] == {'s': 0} and r['tight'] == ['s']
    # dynamic equal-string witness: equal sequences share one spread
    dyn = ''.join(['s', '1'])
    r = m.translate([(dyn, 1), (''.join(['s', '1']), 2),
                     (''.join(['s', '1']), 4)])
    assert r['spreads'] == {'s1': 6} and r['tight'] == []
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['s%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 2), (n, 3)]
    r = m.translate(rows)
    assert r['tight'] == sorted(names)
    assert r['spreads'] == {n: 1 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.translate('nope')
    with pytest.raises(TypeError):
        m.translate(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.translate([('s', 1)] * 101)
    with pytest.raises(TypeError):
        m.translate([('s', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.translate([('s', 1), ('s',)])
    with pytest.raises(TypeError):
        m.translate([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.translate([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.translate([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.translate([('s', '1')])
    with pytest.raises(TypeError):
        m.translate([('s', LyingI())])
    with pytest.raises(TypeError):
        m.translate([('s', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.translate([('s', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.translate([('s', -1)])
    # first bad row pins, mixed failure types
    try:
        m.translate([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.translate([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.translate({'s': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.translate(ListSub([('s', 1)]))
    with pytest.raises(TypeError):
        m.translate([ListSub(('s', 1))])
    # tuple rows accepted exactly like lists
    assert m.translate((('s', 1),)) == m.translate([('s', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.translate([('s', 1), ['s', 2], ('s', 4)])
    assert mixed == m.translate([['s', 1], ('s', 2), ['s', 4]])
    # boundary acceptance pins
    assert m.translate([('abcdefgh', 1)])['spreads'] == {'abcdefgh': 0}
    assert m.translate([('s', 1)] * 100)['total'] == 100
    assert m.translate([('s', 0)])['spreads'] == {'s': 0}
    assert m.translate([('s', 10)])['spreads'] == {'s': 0}
    # default-start pins: unknown sequence starts with no spread
    r = m.translate([('zz', 4)])
    assert r['spreads'] == {'zz': 0} and r['tight'] == ['zz']
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
    ('spread += abs(a - b)', 'spread += a - b'),
    ('spread += abs(a - b)', 'spread = abs(a - b)'),
    ('spread += abs(a - b)', 'spread += abs(a - b) + 1'),
    ('spread += abs(a - b)', 'spread += abs(a + b)'),
    ('for b in vals[i + 1:]:', 'for b in vals:'),
    ('for i, a in enumerate(vals):', 'for i, a in enumerate(vals, 1):'),
    ('spread = 0', 'spread = 1'),
    ('spread <= TIGHT', 'spread < TIGHT'),
    ('spread <= TIGHT', 'spread <= TIGHT + 1'),
    ('TIGHT = 4', 'TIGHT = 3'),
    ('TIGHT = 4', 'TIGHT = 5'),
    ('tight = sorted(', 'tight = list('),
    ('values.setdefault(sequence, []).append(expression)',
     'values.setdefault(sequence, [0]).append(expression)'),
    ('values: dict = {}', "values: dict = {'zz': [1]}"),
    ('spreads = {}', "spreads = {'zz': 9}"),
    ('sequence, expression = row', 'expression, sequence = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(spreads)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(sequence) <= MAX_NAME',
     'not 1 <= len(sequence) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_EXPRESSION = 0', 'MIN_EXPRESSION = 1'),
    ('MAX_EXPRESSION = 10', 'MAX_EXPRESSION = 9'),
    ('not MIN_EXPRESSION <= expression <= MAX_EXPRESSION',
     'not MIN_EXPRESSION < expression < MAX_EXPRESSION'),
    ("'spreads': spreads", "'spreads': tight"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.translate([(S('s'), 5)]), TypeError,
           'row 1: sequence must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.translate('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.translate(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.translate({'s': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.translate([('s', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.translate([('s', 1), 'bad']), TypeError,
           'row 2: expected (sequence, expression) tuple, got str')
    _exact(lambda: m.translate([('s', 1), ('s',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.translate([(1, 1)]), TypeError,
           'row 1: sequence must be str, got int')
    _exact(lambda: m.translate([(True, 1)]), TypeError,
           'row 1: sequence must be str, got bool')
    _exact(lambda: m.translate([('', 1)]), ValueError,
           'row 1: sequence must be 1-8 chars')
    _exact(lambda: m.translate([('abcdefghi', 1)]), ValueError,
           'row 1: sequence must be 1-8 chars')
    _exact(lambda: m.translate([('s', '1')]), TypeError,
           'row 1: expression must be int, got str')
    _exact(lambda: m.translate([('s', True)]), TypeError,
           'row 1: expression must be int, got bool')
    _exact(lambda: m.translate([('s', 11)]), ValueError,
           'row 1: expression must be 0-10, got 11')
    _exact(lambda: m.translate([('s', -1)]), ValueError,
           'row 1: expression must be 0-10, got -1')
    _exact(lambda: m.translate([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: sequence must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 987, mRNA Therapeutics' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: expression bookkeeping only; no translation modeled'
    assert module.NOT_CLAIMED == (
        'does not model codon optimization',
        'does not weight expressions by record order',
        'does not compare sequences against each other',
        'does not cap how many expressions one sequence may hold',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
