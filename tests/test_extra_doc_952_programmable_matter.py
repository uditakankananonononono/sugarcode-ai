"""Mutation and oracle tests for extra_doc.programmable_matter."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_952_programmable_matter.py',
                        'src/sugarcode/extra_doc/programmable_matter.py')

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
        return 2


class ListSub(list):
    pass


def _core(module):
    m = module
    # oracle seeded with row number 952
    assert m.morph([]) == {'total': 0, 'cells': 0, 'mean': 0, 'stress': []}
    # extremes deviate by 5: both stressed
    r = m.morph([('a', 0), ('b', 10)])
    assert r == {'total': 2, 'cells': 2, 'mean': 5, 'stress': ['a', 'b']}
    # deviation of exactly 2 is not stressed (strict boundary)
    r = m.morph([('a', 3), ('b', 7)])
    assert r['stress'] == [] and r['mean'] == 5
    # deviation of 3 is stressed (tolerance pinned at 2, not 3)
    r = m.morph([('a', 2), ('b', 8)])
    assert r['stress'] == ['a', 'b'] and r['mean'] == 5
    # per-cell averaging: a at (2+8)/2 = 5 equals the sheet average
    r = m.morph([('a', 2), ('a', 8), ('b', 5)])
    assert r['stress'] == [] and r['mean'] == 5 and r['cells'] == 2
    # one-sided stress: only the low cell deviates beyond 2
    r = m.morph([('a', 0), ('b', 8)])
    assert r['mean'] == 4 and r['stress'] == ['a', 'b']
    # a lone cell always sits at the average
    r = m.morph([('a', 7)])
    assert r['stress'] == [] and r['mean'] == 7 and r['cells'] == 1
    # mean rounds down: levels 1 and 2 average to 1
    r = m.morph([('a', 1), ('b', 2)])
    assert r['mean'] == 1 and r['stress'] == []
    # dynamic equal-string witness: equal cells merge their records
    dyn = ''.join(['c', '1'])
    r = m.morph([(dyn, 0), (''.join(['c', '1']), 10)])
    assert r['cells'] == 1 and r['stress'] == []  # merged average is 5 = mean
    # wide many-name sort pin (20 cells at the same level)
    names = ['cl%02d' % i for i in range(20)]
    r = m.morph([(n, 5) for n in names])
    assert r['stress'] == [] and r['cells'] == 20 and r['mean'] == 5
    # wide stressed set, sorted: ten low cells and ten high cells
    r = m.morph([(n, 0) for n in names[:10]] + [(n, 10) for n in names[10:]])
    assert r['stress'] == sorted(names) and r['mean'] == 5
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.morph('nope')
    with pytest.raises(TypeError):
        m.morph(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.morph([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.morph([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.morph([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.morph([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.morph([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.morph([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.morph([('a', '1')])
    with pytest.raises(TypeError):
        m.morph([('a', LyingI())])
    with pytest.raises(TypeError):
        m.morph([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.morph([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.morph([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.morph([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.morph([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.morph({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.morph(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.morph([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.morph((('a', 1),)) == m.morph([('a', 1)])
    # boundary acceptance pins
    assert m.morph([('abcdefgh', 1)])['cells'] == 1
    assert m.morph([('a', 1)] * 100)['total'] == 100
    assert m.morph([('a', 0)])['mean'] == 0
    assert m.morph([('a', 10)])['mean'] == 10
    # default-start pins: unknown cell must start at sum 0, count 0
    r = m.morph([('zz', 6), ('zz', 6)])
    assert r['cells'] == 1 and r['stress'] == []
    r = m.morph([('zz', 5)])
    assert r['stress'] == []  # a lone cell sits at the average; count must be 1
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
    ('abs(cell_sum * n - total_level * counts[cell])',
     'cell_sum * n - total_level * counts[cell]'),
    ('> TOLERANCE * n * counts[cell]', '>= TOLERANCE * n * counts[cell]'),
    ('> TOLERANCE * n * counts[cell]', '< TOLERANCE * n * counts[cell]'),
    ('TOLERANCE = 2', 'TOLERANCE = 3'),
    ('TOLERANCE = 2', 'TOLERANCE = 1'),
    ('total_level // n', 'total_level / n'),
    ('total_level // n if n else 0', 'total_level // n'),
    ('sums.get(cell, 0) + level', 'sums.get(cell, 0) - level'),
    ('sums.get(cell, 0)', 'sums.get(cell, 1)'),
    ('counts.get(cell, 0) + 1', 'counts.get(cell, 0) + 2'),
    ('counts.get(cell, 0)', 'counts.get(cell, 1)'),
    ("'cells': len(sums)", "'cells': len(rows)"),
    ("'total': n", "'total': len(sums)"),
    ('cell, level = row', 'level, cell = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MIN_LEVEL = 0', 'MIN_LEVEL = 1'),
    ('MAX_LEVEL = 10', 'MAX_LEVEL = 9'),
    ('not MIN_LEVEL <= level <= MAX_LEVEL', 'not MIN_LEVEL < level < MAX_LEVEL'),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(cell) <= MAX_NAME', 'not 1 <= len(cell) < MAX_NAME'),
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
    assert 'Row 952, Programmable Matter' in module.__doc__


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True


class S(str):
    pass


def _exact(fn, exc_type, expected):
    with pytest.raises(exc_type) as info:
        fn()
    assert str(info.value) == expected


def test_str_subclass_rejected_v2():
    m = _load_code(SRC)
    _exact(lambda: m.morph([(S('a'), 2)]), TypeError,
           'row 1: cell must be str, got S')


def test_error_messages_exact_v2():
    m = _load_code(SRC)
    _exact(lambda: m.morph('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.morph(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.morph({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.morph([('a', 2)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.morph([('a', 2), 'bad']), TypeError,
           'row 2: expected (cell, level) tuple, got str')
    _exact(lambda: m.morph([('a', 2), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.morph([(1, 2)]), TypeError,
           'row 1: cell must be str, got int')
    _exact(lambda: m.morph([(True, 2)]), TypeError,
           'row 1: cell must be str, got bool')
    _exact(lambda: m.morph([('', 2)]), ValueError,
           'row 1: cell must be 1-8 chars')
    _exact(lambda: m.morph([('abcdefghi', 2)]), ValueError,
           'row 1: cell must be 1-8 chars')
    _exact(lambda: m.morph([('a', '2')]), TypeError,
           'row 1: level must be int, got str')
    _exact(lambda: m.morph([('a', True)]), TypeError,
           'row 1: level must be int, got bool')
    _exact(lambda: m.morph([('a', 11)]), ValueError,
           'row 1: level must be 0-10, got 11')
    _exact(lambda: m.morph([('a', -1)]), ValueError,
           'row 1: level must be 0-10, got -1')
    _exact(lambda: m.morph([('a', 2), ('a', 2), (1, 2)]),
           TypeError, 'row 3: cell must be str, got int')


def test_scope_wording_exact_v2():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: stress detection only; '
                            'no actuation or feedback modeled')
    assert module.NOT_CLAIMED == (
        'does not model cell actuation or locomotion',
        'does not propagate stress between neighbors',
        'does not reshape the sheet',
        'does not weight cells by area',
    )


def test_stress_line_witnesses_v3():
    """Behavior witnesses for the exact cross-multiplied stress line."""
    m = _load_code(SRC)
    # auditor-21 witness: the //-mutant returns ['a', 'b'] here
    r = m.morph([('b', 3), ('a', 7), ('b', 0)])
    assert r == {'total': 3, 'cells': 2, 'mean': 3, 'stress': ['a']}
    # a sits exactly at the tolerance: |1*3 - 9*1| = 6 == 2*3*1, strict >
    # keeps it calm; the //-mutant calls b stressed (6 > 3)
    r = m.morph([('b', 4), ('b', 4), ('a', 1)])
    assert r == {'total': 3, 'cells': 2, 'mean': 3, 'stress': []}
    # two clearly deviating cells are stressed under either threshold
    # shape; the cell exactly on the mean stays calm
    r = m.morph([('a', 10), ('b', 0), ('c', 5)])
    assert r['stress'] == ['a', 'b']
    # one record per cell: * and // agree, deviation must still be exact
    r = m.morph([('a', 10), ('b', 0)])
    assert r['stress'] == ['a', 'b']
