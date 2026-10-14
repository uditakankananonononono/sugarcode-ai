"""Mutation and oracle tests for extra_doc.nanomedicine."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_988_nanomedicine.py',
                        'src/sugarcode/extra_doc/nanomedicine.py')

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
    # oracle seeded with row number 988
    assert m.coat([]) == {'total': 0, 'couplings': {}, 'bonded': []}
    # sizes 1, 2, 3 couple to 1*2 + 2*3 = 8 and bond: boundary
    r = m.coat([('p', 1), ('p', 2), ('p', 3)])
    assert r == {'total': 3, 'couplings': {'p': 8}, 'bonded': ['p']}
    # 2, 2 couple to 4
    r = m.coat([('p', 2), ('p', 2)])
    assert r == {'total': 2, 'couplings': {'p': 4}, 'bonded': []}
    # 1, 1, 6 couple to 7 and do not bond: boundary just below
    r = m.coat([('p', 1), ('p', 1), ('p', 6)])
    assert r == {'total': 3, 'couplings': {'p': 7}, 'bonded': []}
    # 3, 3 couple to 9 and bond: boundary just above
    r = m.coat([('p', 3), ('p', 3)])
    assert r == {'total': 2, 'couplings': {'p': 9}, 'bonded': ['p']}
    # 3, 0, 3 couple to 0
    r = m.coat([('p', 3), ('p', 0), ('p', 3)])
    assert r == {'total': 3, 'couplings': {'p': 0}, 'bonded': []}
    # 1, 2, 3, 4 couple to 2 + 6 + 12 = 20
    r = m.coat([('p', 1), ('p', 2), ('p', 3), ('p', 4)])
    assert r == {'total': 4, 'couplings': {'p': 20}, 'bonded': ['p']}
    # a lone size couples to 0
    r = m.coat([('p', 5)])
    assert r == {'total': 1, 'couplings': {'p': 0}, 'bonded': []}
    # order matters: 1, 2, 4 couples to 10 while 2, 4, 1 couples to 12
    assert m.coat([('p', 1), ('p', 2), ('p', 4)])['couplings'] == {'p': 10}
    assert m.coat([('p', 2), ('p', 4), ('p', 1)])['couplings'] == {'p': 12}
    # each particle keeps its own coupling
    r = m.coat([('a', 1), ('b', 2), ('a', 2), ('a', 3)])
    assert r == {'total': 4, 'couplings': {'a': 8, 'b': 0},
                 'bonded': ['a']}
    # boundary sizes
    r = m.coat([('p', 0), ('p', 10)])
    assert r['couplings'] == {'p': 0}
    r = m.coat([('p', 10), ('p', 10)])
    assert r['couplings'] == {'p': 100} and r['bonded'] == ['p']
    # dynamic equal-string witness: equal particles share one coupling
    dyn = ''.join(['p', '1'])
    r = m.coat([(dyn, 1), (''.join(['p', '1']), 2),
                (''.join(['p', '1']), 3)])
    assert r['couplings'] == {'p1': 8} and r['bonded'] == ['p1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['p%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 3), (n, 3)]
    r = m.coat(rows)
    assert r['bonded'] == sorted(names)
    assert r['couplings'] == {n: 9 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.coat('nope')
    with pytest.raises(TypeError):
        m.coat(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.coat([('p', 1)] * 101)
    with pytest.raises(TypeError):
        m.coat([('p', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.coat([('p', 1), ('p',)])
    with pytest.raises(TypeError):
        m.coat([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.coat([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.coat([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.coat([('p', '1')])
    with pytest.raises(TypeError):
        m.coat([('p', LyingI())])
    with pytest.raises(TypeError):
        m.coat([('p', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.coat([('p', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.coat([('p', -1)])
    # first bad row pins, mixed failure types
    try:
        m.coat([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.coat([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.coat({'p': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.coat(ListSub([('p', 1)]))
    with pytest.raises(TypeError):
        m.coat([ListSub(('p', 1))])
    # tuple rows accepted exactly like lists
    assert m.coat((('p', 1),)) == m.coat([('p', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.coat([('p', 1), ['p', 2], ('p', 3)])
    assert mixed == m.coat([['p', 1], ('p', 2), ['p', 3]])
    # boundary acceptance pins
    assert m.coat([('abcdefgh', 1)])['couplings'] == {'abcdefgh': 0}
    assert m.coat([('p', 1)] * 100)['total'] == 100
    assert m.coat([('p', 0)])['couplings'] == {'p': 0}
    assert m.coat([('p', 10)])['couplings'] == {'p': 0}
    # default-start pins: unknown particle starts with no coupling
    r = m.coat([('zz', 4)])
    assert r['couplings'] == {'zz': 0} and r['bonded'] == []
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
    ('coupling += vals[i] * vals[i + 1]',
     'coupling += vals[i] + vals[i + 1]'),
    ('coupling += vals[i] * vals[i + 1]',
     'coupling = vals[i] * vals[i + 1]'),
    ('vals[i] * vals[i + 1]', 'vals[i] * vals[i]'),
    ('range(len(vals) - 1)', 'range(len(vals))'),
    ('range(len(vals) - 1)', 'range(1, len(vals) - 1)'),
    ('coupling = 0', 'coupling = 1'),
    ('coupling >= BOND', 'coupling > BOND'),
    ('coupling >= BOND', 'coupling >= BOND + 1'),
    ('BOND = 8', 'BOND = 7'),
    ('BOND = 8', 'BOND = 9'),
    ('bonded = sorted(', 'bonded = list('),
    ('values.setdefault(particle, []).append(size)',
     'values.setdefault(particle, [1]).append(size)'),
    ('values: dict = {}', "values: dict = {'zz': [2, 3]}"),
    ('couplings = {}', "couplings = {'zz': 9}"),
    ('particle, size = row', 'size, particle = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(couplings)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(particle) <= MAX_NAME',
     'not 1 <= len(particle) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_SIZE = 0', 'MIN_SIZE = 1'),
    ('MAX_SIZE = 10', 'MAX_SIZE = 9'),
    ('not MIN_SIZE <= size <= MAX_SIZE',
     'not MIN_SIZE < size < MAX_SIZE'),
    ("'couplings': couplings", "'couplings': values"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.coat([(S('p'), 5)]), TypeError,
           'row 1: particle must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.coat('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.coat(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.coat({'p': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.coat([('p', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.coat([('p', 1), 'bad']), TypeError,
           'row 2: expected (particle, size) tuple, got str')
    _exact(lambda: m.coat([('p', 1), ('p',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.coat([(1, 1)]), TypeError,
           'row 1: particle must be str, got int')
    _exact(lambda: m.coat([(True, 1)]), TypeError,
           'row 1: particle must be str, got bool')
    _exact(lambda: m.coat([('', 1)]), ValueError,
           'row 1: particle must be 1-8 chars')
    _exact(lambda: m.coat([('abcdefghi', 1)]), ValueError,
           'row 1: particle must be 1-8 chars')
    _exact(lambda: m.coat([('p', '1')]), TypeError,
           'row 1: size must be int, got str')
    _exact(lambda: m.coat([('p', True)]), TypeError,
           'row 1: size must be int, got bool')
    _exact(lambda: m.coat([('p', 11)]), ValueError,
           'row 1: size must be 0-10, got 11')
    _exact(lambda: m.coat([('p', -1)]), ValueError,
           'row 1: size must be 0-10, got -1')
    _exact(lambda: m.coat([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: particle must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 988, Nanomedicine' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: coating bookkeeping only; no drug loading modeled'
    assert module.NOT_CLAIMED == (
        'does not model circulation half-life',
        'does not weight sizes beyond neighbouring pairs',
        'does not compare particles against each other',
        'does not cap how many coats one particle may hold',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
