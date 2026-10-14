"""Mutation and oracle tests for extra_doc.neural_prosthetics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_995_neural_prosthetics.py',
                        'src/sugarcode/extra_doc/neural_prosthetics.py')

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
    # oracle seeded with row number 995
    assert m.fire([]) == {'total': 0, 'prefixes': {}, 'trained': []}
    # firings 3, 3, 5, 2, 7 hold for 3 - the later 7 does not extend it
    r = m.fire([('n', 3), ('n', 3), ('n', 5), ('n', 2), ('n', 7)])
    assert r == {'total': 5, 'prefixes': {'n': 3}, 'trained': ['n']}
    # 1, 0 hold for 1
    r = m.fire([('n', 1), ('n', 0)])
    assert r == {'total': 2, 'prefixes': {'n': 1}, 'trained': []}
    # 5, 5, 5 hold for 3 and train: boundary on the trained side
    r = m.fire([('n', 5), ('n', 5), ('n', 5)])
    assert r == {'total': 3, 'prefixes': {'n': 3}, 'trained': ['n']}
    # 2, 2 hold for 2: boundary just below trained
    r = m.fire([('n', 2), ('n', 2)])
    assert r == {'total': 2, 'prefixes': {'n': 2}, 'trained': []}
    # 1, 2 hold for 2
    r = m.fire([('n', 1), ('n', 2)])
    assert r == {'total': 2, 'prefixes': {'n': 2}, 'trained': []}
    # 1, 2, 3 hold for 3
    r = m.fire([('n', 1), ('n', 2), ('n', 3)])
    assert r == {'total': 3, 'prefixes': {'n': 3}, 'trained': ['n']}
    # 0, 0, 1 hold for 3
    r = m.fire([('n', 0), ('n', 0), ('n', 1)])
    assert r == {'total': 3, 'prefixes': {'n': 3}, 'trained': ['n']}
    # 2, 1 hold for 1
    r = m.fire([('n', 2), ('n', 1)])
    assert r == {'total': 2, 'prefixes': {'n': 1}, 'trained': []}
    # a lone firing holds for 1
    r = m.fire([('n', 7)])
    assert r == {'total': 1, 'prefixes': {'n': 1}, 'trained': []}
    # boundary firings: 10, 10, 10 hold for 3
    r = m.fire([('n', 10), ('n', 10), ('n', 10)])
    assert r['prefixes'] == {'n': 3} and r['trained'] == ['n']
    # each nerve keeps its own prefix
    r = m.fire([('a', 1), ('b', 5), ('a', 2), ('a', 3)])
    assert r == {'total': 4, 'prefixes': {'a': 3, 'b': 1},
                 'trained': ['a']}
    # dynamic equal-string witness: equal nerves share one prefix
    dyn = ''.join(['n', '1'])
    r = m.fire([(dyn, 1), (''.join(['n', '1']), 2),
                (''.join(['n', '1']), 3)])
    assert r['prefixes'] == {'n1': 3} and r['trained'] == ['n1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['n%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 2), (n, 3)]
    r = m.fire(rows)
    assert r['trained'] == sorted(names)
    assert r['prefixes'] == {n: 3 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.fire('nope')
    with pytest.raises(TypeError):
        m.fire(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.fire([('n', 1)] * 101)
    with pytest.raises(TypeError):
        m.fire([('n', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.fire([('n', 1), ('n',)])
    with pytest.raises(TypeError):
        m.fire([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.fire([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.fire([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.fire([('n', '1')])
    with pytest.raises(TypeError):
        m.fire([('n', LyingI())])
    with pytest.raises(TypeError):
        m.fire([('n', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.fire([('n', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.fire([('n', -1)])
    # first bad row pins, mixed failure types
    try:
        m.fire([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.fire([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.fire({'n': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.fire(ListSub([('n', 1)]))
    with pytest.raises(TypeError):
        m.fire([ListSub(('n', 1))])
    # tuple rows accepted exactly like lists
    assert m.fire((('n', 1),)) == m.fire([('n', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.fire([('n', 1), ['n', 2], ('n', 3)])
    assert mixed == m.fire([['n', 1], ('n', 2), ['n', 3]])
    # boundary acceptance pins
    assert m.fire([('abcdefgh', 1)])['prefixes'] == {'abcdefgh': 1}
    assert m.fire([('n', 1)] * 100)['total'] == 100
    assert m.fire([('n', 0)])['prefixes'] == {'n': 1}
    assert m.fire([('n', 10)])['prefixes'] == {'n': 1}
    # default-start pins: unknown nerve starts with a prefix of 1
    r = m.fire([('zz', 1), ('zz', 2)])
    assert r['prefixes'] == {'zz': 2} and r['trained'] == []
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
    ('vals[i] < vals[i - 1]', 'vals[i] <= vals[i - 1]'),
    ('vals[i] < vals[i - 1]', 'vals[i] > vals[i - 1]'),
    ('break', 'pass'),
    ('range(1, len(vals))', 'range(len(vals))'),
    ('length = 1', 'length = 0'),
    ('length = 1', 'length = 2'),
    ('length += 1', 'length += 2'),
    ('length >= TRAINED', 'length > TRAINED'),
    ('length >= TRAINED', 'length >= TRAINED + 1'),
    ('TRAINED = 3', 'TRAINED = 2'),
    ('TRAINED = 3', 'TRAINED = 4'),
    ('trained = sorted(', 'trained = list('),
    ('values.setdefault(nerve, []).append(firing)',
     'values.setdefault(nerve, [9]).append(firing)'),
    ('values: dict = {}', "values: dict = {'zz': [1, 2, 3]}"),
    ('prefixes = {}', "prefixes = {'zz': 5}"),
    ('nerve, firing = row', 'firing, nerve = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(prefixes)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(nerve) <= MAX_NAME',
     'not 1 <= len(nerve) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_FIRING = 0', 'MIN_FIRING = 1'),
    ('MAX_FIRING = 10', 'MAX_FIRING = 9'),
    ('not MIN_FIRING <= firing <= MAX_FIRING',
     'not MIN_FIRING < firing < MAX_FIRING'),
    ("'prefixes': prefixes", "'prefixes': trained"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.fire([(S('n'), 5)]), TypeError,
           'row 1: nerve must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.fire('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.fire(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.fire({'n': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.fire([('n', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.fire([('n', 1), 'bad']), TypeError,
           'row 2: expected (nerve, firing) tuple, got str')
    _exact(lambda: m.fire([('n', 1), ('n',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.fire([(1, 1)]), TypeError,
           'row 1: nerve must be str, got int')
    _exact(lambda: m.fire([(True, 1)]), TypeError,
           'row 1: nerve must be str, got bool')
    _exact(lambda: m.fire([('', 1)]), ValueError,
           'row 1: nerve must be 1-8 chars')
    _exact(lambda: m.fire([('abcdefghi', 1)]), ValueError,
           'row 1: nerve must be 1-8 chars')
    _exact(lambda: m.fire([('n', '1')]), TypeError,
           'row 1: firing must be int, got str')
    _exact(lambda: m.fire([('n', True)]), TypeError,
           'row 1: firing must be int, got bool')
    _exact(lambda: m.fire([('n', 11)]), ValueError,
           'row 1: firing must be 0-10, got 11')
    _exact(lambda: m.fire([('n', -1)]), ValueError,
           'row 1: firing must be 0-10, got -1')
    _exact(lambda: m.fire([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: nerve must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 995, Neural Prosthetics' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: firing bookkeeping only; no neural tissue modeled'
    assert module.NOT_CLAIMED == (
        'does not model membrane potentials',
        'does not let a later rise extend a broken prefix',
        'does not require firings to increase, only not to drop',
        'does not compare nerves against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
