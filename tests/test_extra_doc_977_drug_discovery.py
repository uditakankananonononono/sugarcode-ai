"""Mutation and oracle tests for extra_doc.drug_discovery."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_977_drug_discovery.py',
                        'src/sugarcode/extra_doc/drug_discovery.py')

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
    # oracle seeded with row number 977
    assert m.screen([]) == {'total': 0, 'spans': {}, 'focused': []}
    # potencies 2, 7, 4 span 5 and lose focus
    r = m.screen([('c', 2), ('c', 7), ('c', 4)])
    assert r == {'total': 3, 'spans': {'c': 5}, 'focused': []}
    # 2, 5, 4 span 3 and stay focused
    r = m.screen([('c', 2), ('c', 5), ('c', 4)])
    assert r == {'total': 3, 'spans': {'c': 3}, 'focused': ['c']}
    # the order never matters, so 7, 2, 4 spans 5 too
    r = m.screen([('c', 7), ('c', 2), ('c', 4)])
    assert r['spans'] == {'c': 5} and r['focused'] == []
    # a lone record spans 0
    r = m.screen([('c', 6)])
    assert r == {'total': 1, 'spans': {'c': 0}, 'focused': ['c']}
    # a span of exactly 3 still counts focused
    r = m.screen([('c', 4), ('c', 7)])
    assert r['spans'] == {'c': 3} and r['focused'] == ['c']
    # a span of 4 spills over
    r = m.screen([('c', 4), ('c', 8)])
    assert r['spans'] == {'c': 4} and r['focused'] == []
    # the low and the high can arrive in either order
    r = m.screen([('c', 8), ('c', 4)])
    assert r['spans'] == {'c': 4}
    # equal records span 0
    r = m.screen([('c', 5), ('c', 5)])
    assert r['spans'] == {'c': 0} and r['focused'] == ['c']
    # each compound keeps its own low and high
    r = m.screen([('a', 1), ('b', 8), ('a', 9), ('b', 7)])
    assert r == {'total': 4, 'spans': {'a': 8, 'b': 1}, 'focused': ['b']}
    # boundary potencies
    r = m.screen([('c', 0), ('c', 10)])
    assert r['spans'] == {'c': 10} and r['focused'] == []
    # dynamic equal-string witness: equal compounds share one window
    dyn = ''.join(['c', '1'])
    r = m.screen([(dyn, 3), (''.join(['c', '1']), 5)])
    assert r['spans'] == {'c1': 2} and r['focused'] == ['c1']
    # wide many-name sort pin, inserted in reverse order (20 compounds)
    names = ['c%02d' % i for i in range(20)]
    r = m.screen([(n, 3) for n in reversed(names)])
    assert r['focused'] == sorted(names)
    assert r['spans'] == {n: 0 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.screen('nope')
    with pytest.raises(TypeError):
        m.screen(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.screen([('c', 1)] * 101)
    with pytest.raises(TypeError):
        m.screen([('c', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.screen([('c', 1), ('c',)])
    with pytest.raises(TypeError):
        m.screen([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.screen([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.screen([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.screen([('c', '1')])
    with pytest.raises(TypeError):
        m.screen([('c', LyingI())])
    with pytest.raises(TypeError):
        m.screen([('c', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.screen([('c', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.screen([('c', -1)])
    # first bad row pins, mixed failure types
    try:
        m.screen([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.screen([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.screen({'c': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.screen(ListSub([('c', 1)]))
    with pytest.raises(TypeError):
        m.screen([ListSub(('c', 1))])
    # tuple rows accepted exactly like lists
    assert m.screen((('c', 1),)) == m.screen([('c', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.screen([('c', 2), ['c', 5]])
    assert mixed == m.screen([['c', 2], ('c', 5)])
    # boundary acceptance pins
    assert m.screen([('abcdefgh', 1)])['spans'] == {'abcdefgh': 0}
    assert m.screen([('c', 1)] * 100)['total'] == 100
    assert m.screen([('c', 0)])['spans'] == {'c': 0}
    assert m.screen([('c', 10)])['spans'] == {'c': 0}
    # default-start pins: unknown compound opens a zero-width window
    r = m.screen([('zz', 3), ('zz', 6)])
    assert r['spans'] == {'zz': 3} and r['focused'] == ['zz']
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
    ('lows[compound] = min(lows[compound], potency)',
     'lows[compound] = max(lows[compound], potency)'),
    ('highs[compound] = max(highs[compound], potency)',
     'highs[compound] = min(highs[compound], potency)'),
    ('highs[compound] = max(highs[compound], potency)',
     'highs[compound] = potency'),
    ('highs[compound] - lows[compound]',
     'lows[compound] - highs[compound]'),
    ('if compound not in lows:', 'if compound in lows:'),
    ('lows[compound] = potency', 'lows[compound] = potency + 1'),
    ('span <= FOCUS', 'span < FOCUS'),
    ('FOCUS = 3', 'FOCUS = 2'),
    ('FOCUS = 3', 'FOCUS = 4'),
    ('focused = sorted(', 'focused = list('),
    ('MIN_POTENCY = 0', 'MIN_POTENCY = 1'),
    ('MAX_POTENCY = 10', 'MAX_POTENCY = 9'),
    ('not MIN_POTENCY <= potency <= MAX_POTENCY',
     'not MIN_POTENCY < potency < MAX_POTENCY'),
    ('compound, potency = row', 'potency, compound = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(lows)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(compound) <= MAX_NAME',
     'not 1 <= len(compound) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'spans': spans", "'spans': highs"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.screen([(S('c'), 5)]), TypeError,
           'row 1: compound must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.screen('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.screen(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.screen({'c': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.screen([('c', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.screen([('c', 1), 'bad']), TypeError,
           'row 2: expected (compound, potency) tuple, got str')
    _exact(lambda: m.screen([('c', 1), ('c',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.screen([(1, 1)]), TypeError,
           'row 1: compound must be str, got int')
    _exact(lambda: m.screen([(True, 1)]), TypeError,
           'row 1: compound must be str, got bool')
    _exact(lambda: m.screen([('', 1)]), ValueError,
           'row 1: compound must be 1-8 chars')
    _exact(lambda: m.screen([('abcdefghi', 1)]), ValueError,
           'row 1: compound must be 1-8 chars')
    _exact(lambda: m.screen([('c', '1')]), TypeError,
           'row 1: potency must be int, got str')
    _exact(lambda: m.screen([('c', True)]), TypeError,
           'row 1: potency must be int, got bool')
    _exact(lambda: m.screen([('c', 11)]), ValueError,
           'row 1: potency must be 0-10, got 11')
    _exact(lambda: m.screen([('c', -1)]), ValueError,
           'row 1: potency must be 0-10, got -1')
    _exact(lambda: m.screen([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: compound must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 977, Drug Discovery' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: potency bookkeeping only; no pharmacology modeled'
    assert module.NOT_CLAIMED == (
        'does not model dose response curves',
        'does not weight potency by record order',
        'does not compare compounds against each other',
        'does not cap the potency during accumulation',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
