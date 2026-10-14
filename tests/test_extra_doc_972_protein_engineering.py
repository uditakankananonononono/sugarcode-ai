"""Mutation and oracle tests for extra_doc.protein_engineering."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_972_protein_engineering.py',
                        'src/sugarcode/extra_doc/protein_engineering.py')

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
    # oracle seeded with row number 972
    assert m.fold([]) == {'total': 0, 'modes': {}, 'stable': []}
    # deltas 3, 2, 3, 2 tie and the smaller delta 2 reads as the mode
    r = m.fold([('p', 3), ('p', 2), ('p', 3), ('p', 2)])
    assert r == {'total': 4, 'modes': {'p': 2}, 'stable': ['p']}
    # deltas -1, -1, 2 give a mode of -1 and lose stable
    r = m.fold([('p', -1), ('p', -1), ('p', 2)])
    assert r == {'total': 3, 'modes': {'p': -1}, 'stable': []}
    # a lone delta is its own mode
    r = m.fold([('p', -2)])
    assert r == {'total': 1, 'modes': {'p': -2}, 'stable': []}
    # a mode of exactly 0 still counts stable
    r = m.fold([('p', 0), ('p', 0), ('p', 1)])
    assert r['modes'] == {'p': 0} and r['stable'] == ['p']
    # a lone delta of 0 is stable too
    r = m.fold([('p', 0)])
    assert r['modes'] == {'p': 0} and r['stable'] == ['p']
    # the modal delta is the most frequent, not the largest count base
    r = m.fold([('p', 3), ('p', 3), ('p', 2)])
    assert r['modes'] == {'p': 3}
    # deltas 1, 2, 3 all appear once and the mode is 1
    r = m.fold([('p', 1), ('p', 2), ('p', 3)])
    assert r['modes'] == {'p': 1}
    # each protein keeps its own tally
    r = m.fold([('a', 1), ('b', -3), ('a', 1), ('b', -3), ('b', -3)])
    assert r == {'total': 5, 'modes': {'a': 1, 'b': -3}, 'stable': ['a']}
    # boundary deltas
    r = m.fold([('p', 5), ('p', -5), ('p', -5)])
    assert r['modes'] == {'p': -5} and r['stable'] == []
    # dynamic equal-string witness: equal proteins share one tally
    dyn = ''.join(['p', '1'])
    r = m.fold([(dyn, 4), (''.join(['p', '1']), 4), (''.join(['p', '1']), -1)])
    assert r['modes'] == {'p1': 4} and r['stable'] == ['p1']
    # wide many-name sort pin, inserted in reverse order (20 proteins)
    names = ['p%02d' % i for i in range(20)]
    r = m.fold([(n, 1) for n in reversed(names)])
    assert r['stable'] == sorted(names)
    assert r['modes'] == {n: 1 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.fold('nope')
    with pytest.raises(TypeError):
        m.fold(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.fold([('p', 1)] * 101)
    with pytest.raises(TypeError):
        m.fold([('p', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.fold([('p', 1), ('p',)])
    with pytest.raises(TypeError):
        m.fold([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.fold([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.fold([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.fold([('p', '1')])
    with pytest.raises(TypeError):
        m.fold([('p', LyingI())])
    with pytest.raises(TypeError):
        m.fold([('p', True)])
    with pytest.raises(ValueError, match='-5-5'):
        m.fold([('p', 6)])
    with pytest.raises(ValueError, match='-5-5'):
        m.fold([('p', -6)])
    # first bad row pins, mixed failure types
    try:
        m.fold([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.fold([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.fold({'p': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.fold(ListSub([('p', 1)]))
    with pytest.raises(TypeError):
        m.fold([ListSub(('p', 1))])
    # tuple rows accepted exactly like lists
    assert m.fold((('p', 1),)) == m.fold([('p', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.fold([('p', 3), ['p', 2]])
    assert mixed == m.fold([['p', 3], ('p', 2)])
    # boundary acceptance pins
    assert m.fold([('abcdefgh', 1)])['modes'] == {'abcdefgh': 1}
    assert m.fold([('p', 1)] * 100)['total'] == 100
    assert m.fold([('p', -5)])['modes'] == {'p': -5}
    assert m.fold([('p', 5)])['modes'] == {'p': 5}
    # default-start pins: unknown protein starts from an empty tally
    r = m.fold([('zz', 2), ('zz', -1), ('zz', 2)])
    assert r['modes'] == {'zz': 2} and r['stable'] == ['zz']
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
    ('best = max(counts.values())', 'best = min(counts.values())'),
    ('modes[protein] = min(delta for delta, count in counts.items()',
     'modes[protein] = max(delta for delta, count in counts.items()'),
    ('if count == best', 'if count != best'),
    ('if protein not in tallies:', 'if protein in tallies:'),
    ('tallies[protein] = {}', 'tallies[protein] = {0: 1}'),
    ('tallies[protein][delta] = tallies[protein].get(delta, 0) + 1',
     'tallies[protein][delta] = tallies[protein].get(delta, 0)'),
    ('mode >= 0', 'mode > 0'),
    ('stable = sorted(', 'stable = list('),
    ('MIN_DELTA = -5', 'MIN_DELTA = -4'),
    ('MAX_DELTA = 5', 'MAX_DELTA = 4'),
    ('not MIN_DELTA <= delta <= MAX_DELTA',
     'not MIN_DELTA < delta < MAX_DELTA'),
    ('protein, delta = row', 'delta, protein = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(tallies)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(protein) <= MAX_NAME',
     'not 1 <= len(protein) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'modes': modes", "'modes': tallies"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.fold([(S('p'), 5)]), TypeError,
           'row 1: protein must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.fold('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.fold(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.fold({'p': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.fold([('p', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.fold([('p', 1), 'bad']), TypeError,
           'row 2: expected (protein, delta) tuple, got str')
    _exact(lambda: m.fold([('p', 1), ('p',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.fold([(1, 1)]), TypeError,
           'row 1: protein must be str, got int')
    _exact(lambda: m.fold([(True, 1)]), TypeError,
           'row 1: protein must be str, got bool')
    _exact(lambda: m.fold([('', 1)]), ValueError,
           'row 1: protein must be 1-8 chars')
    _exact(lambda: m.fold([('abcdefghi', 1)]), ValueError,
           'row 1: protein must be 1-8 chars')
    _exact(lambda: m.fold([('p', '1')]), TypeError,
           'row 1: delta must be int, got str')
    _exact(lambda: m.fold([('p', True)]), TypeError,
           'row 1: delta must be int, got bool')
    _exact(lambda: m.fold([('p', 6)]), ValueError,
           'row 1: delta must be -5-5, got 6')
    _exact(lambda: m.fold([('p', -6)]), ValueError,
           'row 1: delta must be -5-5, got -6')
    _exact(lambda: m.fold([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: protein must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 972, Protein Engineering' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: delta tallying only; no folding physics modeled'
    assert module.NOT_CLAIMED == (
        'does not model thermodynamic stability',
        'does not weight deltas by record order',
        'does not average the deltas',
        'does not compare proteins against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
