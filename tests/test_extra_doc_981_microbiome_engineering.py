"""Mutation and oracle tests for extra_doc.microbiome_engineering."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_981_microbiome_engineering.py',
                        'src/sugarcode/extra_doc/microbiome_engineering.py')

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
    # oracle seeded with row number 981
    assert m.seed([]) == {'total': 0, 'summits': {}, 'early': []}
    # abundances 3, 5, 5 summit at record 2, the first peak appearance
    r = m.seed([('s', 3), ('s', 5), ('s', 5)])
    assert r == {'total': 3, 'summits': {'s': 2}, 'early': ['s']}
    # 5, 3 summit at 1
    r = m.seed([('s', 5), ('s', 3)])
    assert r == {'total': 2, 'summits': {'s': 1}, 'early': ['s']}
    # 1, 2, 3 summit at 3 and miss the early window
    r = m.seed([('s', 1), ('s', 2), ('s', 3)])
    assert r == {'total': 3, 'summits': {'s': 3}, 'early': []}
    # a lone record summits at 1
    r = m.seed([('s', 7)])
    assert r == {'total': 1, 'summits': {'s': 1}, 'early': ['s']}
    # a summit at record 2 still counts early
    r = m.seed([('s', 1), ('s', 4), ('s', 2)])
    assert r['summits'] == {'s': 2} and r['early'] == ['s']
    # the peak may be retaken later without moving the summit
    r = m.seed([('s', 5), ('s', 1), ('s', 5), ('s', 2)])
    assert r['summits'] == {'s': 1}
    # a new higher peak moves the summit
    r = m.seed([('s', 5), ('s', 1), ('s', 6)])
    assert r['summits'] == {'s': 3} and r['early'] == []
    # each strain keeps its own count and summit
    r = m.seed([('a', 1), ('b', 9), ('a', 2), ('b', 1)])
    assert r == {'total': 4, 'summits': {'a': 2, 'b': 1},
                 'early': ['a', 'b']}
    # boundary abundances
    r = m.seed([('s', 0), ('s', 10)])
    assert r['summits'] == {'s': 2}
    # dynamic equal-string witness: equal strains share one summit
    dyn = ''.join(['s', '1'])
    r = m.seed([(dyn, 1), (''.join(['s', '1']), 4)])
    assert r['summits'] == {'s1': 2} and r['early'] == ['s1']
    # wide many-name sort pin, inserted in reverse order (20 strains)
    names = ['s%02d' % i for i in range(20)]
    r = m.seed([(n, 4) for n in reversed(names)])
    assert r['early'] == sorted(names)
    assert r['summits'] == {n: 1 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.seed('nope')
    with pytest.raises(TypeError):
        m.seed(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.seed([('s', 1)] * 101)
    with pytest.raises(TypeError):
        m.seed([('s', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.seed([('s', 1), ('s',)])
    with pytest.raises(TypeError):
        m.seed([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.seed([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.seed([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.seed([('s', '1')])
    with pytest.raises(TypeError):
        m.seed([('s', LyingI())])
    with pytest.raises(TypeError):
        m.seed([('s', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.seed([('s', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.seed([('s', -1)])
    # first bad row pins, mixed failure types
    try:
        m.seed([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.seed([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.seed({'s': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.seed(ListSub([('s', 1)]))
    with pytest.raises(TypeError):
        m.seed([ListSub(('s', 1))])
    # tuple rows accepted exactly like lists
    assert m.seed((('s', 1),)) == m.seed([('s', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.seed([('s', 1), ['s', 4]])
    assert mixed == m.seed([['s', 1], ('s', 4)])
    # boundary acceptance pins
    assert m.seed([('abcdefgh', 1)])['summits'] == {'abcdefgh': 1}
    assert m.seed([('s', 1)] * 100)['total'] == 100
    assert m.seed([('s', 0)])['summits'] == {'s': 1}
    assert m.seed([('s', 10)])['summits'] == {'s': 1}
    # default-start pins: unknown strain starts its count at 1
    r = m.seed([('zz', 1), ('zz', 4)])
    assert r['summits'] == {'zz': 2} and r['early'] == ['zz']
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
    ('strain not in bests or abundance > bests[strain]',
     'strain not in bests or abundance >= bests[strain]'),
    ('strain not in bests or abundance > bests[strain]',
     'strain not in bests and abundance > bests[strain]'),
    ('counts.get(strain, 0) + 1', 'counts.get(strain, 0)'),
    ('counts.get(strain, 0) + 1', 'counts.get(strain, 1) + 1'),
    ('bests[strain] = abundance', 'bests[strain] = abundance + 1'),
    ('summits[strain] = counts[strain]', 'summits[strain] = index'),
    ('position <= EARLY', 'position < EARLY'),
    ('EARLY = 2', 'EARLY = 1'),
    ('EARLY = 2', 'EARLY = 3'),
    ('early = sorted(', 'early = list('),
    ('MIN_ABUNDANCE = 0', 'MIN_ABUNDANCE = 1'),
    ('MAX_ABUNDANCE = 10', 'MAX_ABUNDANCE = 9'),
    ('not MIN_ABUNDANCE <= abundance <= MAX_ABUNDANCE',
     'not MIN_ABUNDANCE < abundance < MAX_ABUNDANCE'),
    ('strain, abundance = row', 'abundance, strain = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(summits)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(strain) <= MAX_NAME',
     'not 1 <= len(strain) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'summits': summits", "'summits': bests"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.seed([(S('s'), 5)]), TypeError,
           'row 1: strain must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.seed('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.seed(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.seed({'s': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.seed([('s', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.seed([('s', 1), 'bad']), TypeError,
           'row 2: expected (strain, abundance) tuple, got str')
    _exact(lambda: m.seed([('s', 1), ('s',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.seed([(1, 1)]), TypeError,
           'row 1: strain must be str, got int')
    _exact(lambda: m.seed([(True, 1)]), TypeError,
           'row 1: strain must be str, got bool')
    _exact(lambda: m.seed([('', 1)]), ValueError,
           'row 1: strain must be 1-8 chars')
    _exact(lambda: m.seed([('abcdefghi', 1)]), ValueError,
           'row 1: strain must be 1-8 chars')
    _exact(lambda: m.seed([('s', '1')]), TypeError,
           'row 1: abundance must be int, got str')
    _exact(lambda: m.seed([('s', True)]), TypeError,
           'row 1: abundance must be int, got bool')
    _exact(lambda: m.seed([('s', 11)]), ValueError,
           'row 1: abundance must be 0-10, got 11')
    _exact(lambda: m.seed([('s', -1)]), ValueError,
           'row 1: abundance must be 0-10, got -1')
    _exact(lambda: m.seed([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: strain must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 981, Microbiome Engineering' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: abundance bookkeeping only; no ecology modeled'
    assert module.NOT_CLAIMED == (
        'does not model species interactions',
        'does not weight abundance by record order',
        'does not compare strains against each other',
        'does not read records after the summit',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
