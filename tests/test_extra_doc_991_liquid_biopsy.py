"""Mutation and oracle tests for extra_doc.liquid_biopsy."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_991_liquid_biopsy.py',
                        'src/sugarcode/extra_doc/liquid_biopsy.py')

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
    # oracle seeded with row number 991
    assert m.detect([]) == {'total': 0, 'risers': {}, 'risen': []}
    # readings 3, 5, 2, 7 rise twice and mark risen
    r = m.detect([('m', 3), ('m', 5), ('m', 2), ('m', 7)])
    assert r == {'total': 4, 'risers': {'m': 2}, 'risen': ['m']}
    # 3, 3 rise 0 since equal is not above
    r = m.detect([('m', 3), ('m', 3)])
    assert r == {'total': 2, 'risers': {'m': 0}, 'risen': []}
    # 3, 3, 5 rise 1: the equal reading does not count, the 5 does
    r = m.detect([('m', 3), ('m', 3), ('m', 5)])
    assert r == {'total': 3, 'risers': {'m': 1}, 'risen': []}
    # 5, 3 rise 0
    r = m.detect([('m', 5), ('m', 3)])
    assert r == {'total': 2, 'risers': {'m': 0}, 'risen': []}
    # 1, 2 rise 1: boundary just below risen
    r = m.detect([('m', 1), ('m', 2)])
    assert r == {'total': 2, 'risers': {'m': 1}, 'risen': []}
    # 3, 4, 4 rise 2 and mark risen: boundary on the risen side
    r = m.detect([('m', 3), ('m', 4), ('m', 4)])
    assert r == {'total': 3, 'risers': {'m': 2}, 'risen': ['m']}
    # 10, 0 rise 0
    r = m.detect([('m', 10), ('m', 0)])
    assert r == {'total': 2, 'risers': {'m': 0}, 'risen': []}
    # 3, 1, 2 rise 0 because a later dip does not lower the baseline
    r = m.detect([('m', 3), ('m', 1), ('m', 2)])
    assert r == {'total': 3, 'risers': {'m': 0}, 'risen': []}
    # a lone reading rises 0: the baseline itself never counts
    r = m.detect([('m', 7)])
    assert r == {'total': 1, 'risers': {'m': 0}, 'risen': []}
    # boundary levels: 0, 10 rise 1
    r = m.detect([('m', 0), ('m', 10)])
    assert r['risers'] == {'m': 1}
    # each marker keeps its own baseline
    r = m.detect([('a', 1), ('b', 9), ('a', 2), ('a', 3)])
    assert r == {'total': 4, 'risers': {'a': 2, 'b': 0},
                 'risen': ['a']}
    # order matters: 1, 2 rises once while 2, 1 never rises
    assert m.detect([('m', 1), ('m', 2)])['risers'] == {'m': 1}
    assert m.detect([('m', 2), ('m', 1)])['risers'] == {'m': 0}
    # dynamic equal-string witness: equal markers share one baseline
    dyn = ''.join(['m', '1'])
    r = m.detect([(dyn, 3), (''.join(['m', '1']), 4),
                  (''.join(['m', '1']), 4)])
    assert r['risers'] == {'m1': 2} and r['risen'] == ['m1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['m%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 2), (n, 3)]
    r = m.detect(rows)
    assert r['risen'] == sorted(names)
    assert r['risers'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.detect('nope')
    with pytest.raises(TypeError):
        m.detect(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.detect([('m', 1)] * 101)
    with pytest.raises(TypeError):
        m.detect([('m', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.detect([('m', 1), ('m',)])
    with pytest.raises(TypeError):
        m.detect([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.detect([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.detect([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.detect([('m', '1')])
    with pytest.raises(TypeError):
        m.detect([('m', LyingI())])
    with pytest.raises(TypeError):
        m.detect([('m', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.detect([('m', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.detect([('m', -1)])
    # first bad row pins, mixed failure types
    try:
        m.detect([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.detect([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.detect({'m': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.detect(ListSub([('m', 1)]))
    with pytest.raises(TypeError):
        m.detect([ListSub(('m', 1))])
    # tuple rows accepted exactly like lists
    assert m.detect((('m', 1),)) == m.detect([('m', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.detect([('m', 3), ['m', 4], ('m', 4)])
    assert mixed == m.detect([['m', 3], ('m', 4), ['m', 4]])
    # boundary acceptance pins
    assert m.detect([('abcdefgh', 1)])['risers'] == {'abcdefgh': 0}
    assert m.detect([('m', 1)] * 100)['total'] == 100
    assert m.detect([('m', 0)])['risers'] == {'m': 0}
    assert m.detect([('m', 10)])['risers'] == {'m': 0}
    # default-start pins: unknown marker starts with no rises
    r = m.detect([('zz', 3), ('zz', 4)])
    assert r['risers'] == {'zz': 1} and r['risen'] == []
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
    ('v > base', 'v >= base'),
    ('v > base', 'v < base'),
    ('base = vals[0]', 'base = vals[-1]'),
    ('base = vals[0]', 'base = min(vals)'),
    ('base = vals[0]', 'base = 0'),
    ('for v in vals[1:]:', 'for v in vals[2:]:'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('count >= RISEN', 'count > RISEN'),
    ('count >= RISEN', 'count >= RISEN + 1'),
    ('RISEN = 2', 'RISEN = 1'),
    ('RISEN = 2', 'RISEN = 3'),
    ('risen = sorted(', 'risen = list('),
    ('values.setdefault(marker, []).append(level)',
     'values.setdefault(marker, [0]).append(level)'),
    ('values: dict = {}', "values: dict = {'zz': [3, 5]}"),
    ('risers = {}', "risers = {'zz': 5}"),
    ('marker, level = row', 'level, marker = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(risers)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(marker) <= MAX_NAME',
     'not 1 <= len(marker) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_LEVEL = 0', 'MIN_LEVEL = 1'),
    ('MAX_LEVEL = 10', 'MAX_LEVEL = 9'),
    ('not MIN_LEVEL <= level <= MAX_LEVEL',
     'not MIN_LEVEL < level < MAX_LEVEL'),
    ("'risers': risers", "'risers': risen"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.detect([(S('m'), 5)]), TypeError,
           'row 1: marker must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.detect('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.detect(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.detect({'m': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.detect([('m', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.detect([('m', 1), 'bad']), TypeError,
           'row 2: expected (marker, level) tuple, got str')
    _exact(lambda: m.detect([('m', 1), ('m',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.detect([(1, 1)]), TypeError,
           'row 1: marker must be str, got int')
    _exact(lambda: m.detect([(True, 1)]), TypeError,
           'row 1: marker must be str, got bool')
    _exact(lambda: m.detect([('', 1)]), ValueError,
           'row 1: marker must be 1-8 chars')
    _exact(lambda: m.detect([('abcdefghi', 1)]), ValueError,
           'row 1: marker must be 1-8 chars')
    _exact(lambda: m.detect([('m', '1')]), TypeError,
           'row 1: level must be int, got str')
    _exact(lambda: m.detect([('m', True)]), TypeError,
           'row 1: level must be int, got bool')
    _exact(lambda: m.detect([('m', 11)]), ValueError,
           'row 1: level must be 0-10, got 11')
    _exact(lambda: m.detect([('m', -1)]), ValueError,
           'row 1: level must be 0-10, got -1')
    _exact(lambda: m.detect([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: marker must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 991, Liquid Biopsy' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: marker bookkeeping only; no assay chemistry modeled'
    assert module.NOT_CLAIMED == (
        'does not model marker half-life',
        'does not count the baseline reading itself',
        'does not weight rises by how far they climb',
        'does not compare markers against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
