"""Mutation and oracle tests for extra_doc.optogenetics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_999_optogenetics.py',
                        'src/sugarcode/extra_doc/optogenetics.py')

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
    # oracle seeded with row number 999
    assert m.flash([]) == {'total': 0, 'echoes': {}, 'echoing': []}
    # flashes 1, 2, 2, 3, 3, 3 echo 2 levels and read echoing
    r = m.flash([('c', 1), ('c', 2), ('c', 2), ('c', 3), ('c', 3),
                 ('c', 3)])
    assert r == {'total': 6, 'echoes': {'c': 2}, 'echoing': ['c']}
    # 5, 5 echo 1
    r = m.flash([('c', 5), ('c', 5)])
    assert r == {'total': 2, 'echoes': {'c': 1}, 'echoing': []}
    # 1, 2, 3 echo 0
    r = m.flash([('c', 1), ('c', 2), ('c', 3)])
    assert r == {'total': 3, 'echoes': {'c': 0}, 'echoing': []}
    # 4, 4, 4, 4 echo 1: one level, however often, is still one echo
    r = m.flash([('c', 4), ('c', 4), ('c', 4), ('c', 4)])
    assert r == {'total': 4, 'echoes': {'c': 1}, 'echoing': []}
    # 1, 1, 2, 2, 3 echo 2 and read echoing: boundary
    r = m.flash([('c', 1), ('c', 1), ('c', 2), ('c', 2), ('c', 3)])
    assert r == {'total': 5, 'echoes': {'c': 2}, 'echoing': ['c']}
    # 3, 3, 3 echo 1: boundary just below echoing
    r = m.flash([('c', 3), ('c', 3), ('c', 3)])
    assert r == {'total': 3, 'echoes': {'c': 1}, 'echoing': []}
    # 0, 0 echo 1: zero is a level too
    r = m.flash([('c', 0), ('c', 0)])
    assert r == {'total': 2, 'echoes': {'c': 1}, 'echoing': []}
    # a lone flash echoes 0
    r = m.flash([('c', 7)])
    assert r == {'total': 1, 'echoes': {'c': 0}, 'echoing': []}
    # boundary flashes: 10, 10, 9, 9 echo 2
    r = m.flash([('c', 10), ('c', 10), ('c', 9), ('c', 9)])
    assert r['echoes'] == {'c': 2} and r['echoing'] == ['c']
    # each channel keeps its own echoes
    r = m.flash([('a', 1), ('b', 2), ('a', 1), ('b', 2), ('a', 3)])
    assert r == {'total': 5, 'echoes': {'a': 1, 'b': 1},
                 'echoing': []}
    # dynamic equal-string witness: equal channels share one count
    dyn = ''.join(['c', '1'])
    r = m.flash([(dyn, 5), (''.join(['c', '1']), 5),
                 (''.join(['c', '1']), 6), (dyn, 6)])
    assert r['echoes'] == {'c1': 2} and r['echoing'] == ['c1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['c%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 1), (n, 2), (n, 2)]
    r = m.flash(rows)
    assert r['echoing'] == sorted(names)
    assert r['echoes'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.flash('nope')
    with pytest.raises(TypeError):
        m.flash(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.flash([('c', 1)] * 101)
    with pytest.raises(TypeError):
        m.flash([('c', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.flash([('c', 1), ('c',)])
    with pytest.raises(TypeError):
        m.flash([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.flash([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.flash([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.flash([('c', '1')])
    with pytest.raises(TypeError):
        m.flash([('c', LyingI())])
    with pytest.raises(TypeError):
        m.flash([('c', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.flash([('c', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.flash([('c', -1)])
    # first bad row pins, mixed failure types
    try:
        m.flash([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.flash([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.flash({'c': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.flash(ListSub([('c', 1)]))
    with pytest.raises(TypeError):
        m.flash([ListSub(('c', 1))])
    # tuple rows accepted exactly like lists
    assert m.flash((('c', 1),)) == m.flash([('c', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.flash([('c', 1), ['c', 2], ('c', 2)])
    assert mixed == m.flash([['c', 1], ('c', 2), ['c', 2]])
    # boundary acceptance pins
    assert m.flash([('abcdefgh', 1)])['echoes'] == {'abcdefgh': 0}
    assert m.flash([('c', 1)] * 100)['total'] == 100
    assert m.flash([('c', 0)])['echoes'] == {'c': 0}
    assert m.flash([('c', 10)])['echoes'] == {'c': 0}
    # default-start pins: unknown channel starts with no echoes
    r = m.flash([('zz', 5), ('zz', 5)])
    assert r['echoes'] == {'zz': 1} and r['echoing'] == []
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
    ('f >= 2', 'f >= 3'),
    ('f >= 2', 'f >= 1'),
    ('freq[v] = freq.get(v, 0) + 1', 'freq[v] = freq.get(v, 0) + 2'),
    ('freq.get(v, 0)', 'freq.get(v, 1)'),
    ('freq = {}', 'freq = {0: 2}'),
    ('freq.values()', 'freq.keys()'),
    ('for v in vals:', 'for v in vals[1:]:'),
    ('count += 1', 'count += 2'),
    ('count = 0', 'count = 1'),
    ('count >= ECHOING', 'count > ECHOING'),
    ('count >= ECHOING', 'count >= ECHOING + 1'),
    ('ECHOING = 2', 'ECHOING = 1'),
    ('ECHOING = 2', 'ECHOING = 3'),
    ('echoing = sorted(', 'echoing = list('),
    ("echoes[channel] = count", "echoes[channel] = len(freq)"),
    ('values.setdefault(channel, []).append(flash)',
     'values.setdefault(channel, [5, 5]).append(flash)'),
    ('values: dict = {}', "values: dict = {'zz': [5, 5]}"),
    ('echoes = {}', "echoes = {'zz': 5}"),
    ('channel, flash = row', 'flash, channel = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(echoes)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(channel) <= MAX_NAME',
     'not 1 <= len(channel) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_FLASH = 0', 'MIN_FLASH = 1'),
    ('MAX_FLASH = 10', 'MAX_FLASH = 9'),
    ('not MIN_FLASH <= flash <= MAX_FLASH',
     'not MIN_FLASH < flash < MAX_FLASH'),
    ("'echoes': echoes", "'echoes': echoing"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.flash([(S('c'), 5)]), TypeError,
           'row 1: channel must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.flash('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.flash(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.flash({'c': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.flash([('c', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.flash([('c', 1), 'bad']), TypeError,
           'row 2: expected (channel, flash) tuple, got str')
    _exact(lambda: m.flash([('c', 1), ('c',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.flash([(1, 1)]), TypeError,
           'row 1: channel must be str, got int')
    _exact(lambda: m.flash([(True, 1)]), TypeError,
           'row 1: channel must be str, got bool')
    _exact(lambda: m.flash([('', 1)]), ValueError,
           'row 1: channel must be 1-8 chars')
    _exact(lambda: m.flash([('abcdefghi', 1)]), ValueError,
           'row 1: channel must be 1-8 chars')
    _exact(lambda: m.flash([('c', '1')]), TypeError,
           'row 1: flash must be int, got str')
    _exact(lambda: m.flash([('c', True)]), TypeError,
           'row 1: flash must be int, got bool')
    _exact(lambda: m.flash([('c', 11)]), ValueError,
           'row 1: flash must be 0-10, got 11')
    _exact(lambda: m.flash([('c', -1)]), ValueError,
           'row 1: flash must be 0-10, got -1')
    _exact(lambda: m.flash([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: channel must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 999, Optogenetics' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: flash bookkeeping only; no channelrhodopsin modeled'
    assert module.NOT_CLAIMED == (
        'does not model light wavelengths',
        'does not count how many times a level repeats, only that it does',
        'does not weight echoes by record order',
        'does not compare channels against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
