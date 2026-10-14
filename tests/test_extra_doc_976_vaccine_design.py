"""Mutation and oracle tests for extra_doc.vaccine_design."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_976_vaccine_design.py',
                        'src/sugarcode/extra_doc/vaccine_design.py')

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
    # oracle seeded with row number 976
    assert m.prime([]) == {'total': 0, 'ladders': {}, 'laddered': []}
    # doses 1, 2, 3 ladder cleanly
    r = m.prime([('v', 1), ('v', 2), ('v', 3)])
    assert r == {'total': 3, 'ladders': {'v': True}, 'laddered': ['v']}
    # 1, 3, 2 break the ladder at the last step
    r = m.prime([('v', 1), ('v', 3), ('v', 2)])
    assert r == {'total': 3, 'ladders': {'v': False}, 'laddered': []}
    # 2, 2 break it because the climb must be strict
    r = m.prime([('v', 2), ('v', 2)])
    assert r['ladders'] == {'v': False} and r['laddered'] == []
    # a lone record is a ladder of one
    r = m.prime([('v', 5)])
    assert r == {'total': 1, 'ladders': {'v': True}, 'laddered': ['v']}
    # a break in the middle is still a break
    r = m.prime([('v', 3), ('v', 1), ('v', 2)])
    assert r['ladders'] == {'v': False}
    # a broken ladder stays broken even if the climb resumes
    r = m.prime([('v', 2), ('v', 1), ('v', 3), ('v', 4)])
    assert r['ladders'] == {'v': False} and r['laddered'] == []
    # boundary steps count
    r = m.prime([('v', 0), ('v', 10)])
    assert r['ladders'] == {'v': True} and r['laddered'] == ['v']
    # one vaccine's stumble never breaks another's ladder
    r = m.prime([('a', 1), ('b', 3), ('a', 2), ('b', 1)])
    assert r == {'total': 4, 'ladders': {'a': True, 'b': False},
                 'laddered': ['a']}
    # dynamic equal-string witness: equal vaccines share one ladder
    dyn = ''.join(['v', '1'])
    r = m.prime([(dyn, 1), (''.join(['v', '1']), 2)])
    assert r['ladders'] == {'v1': True} and r['laddered'] == ['v1']
    # wide many-name sort pin, inserted in reverse order (20 vaccines)
    names = ['v%02d' % i for i in range(20)]
    r = m.prime([(n, 3) for n in reversed(names)] + [(n, 4) for n in names])
    assert r['laddered'] == sorted(names)
    assert r['ladders'] == {n: True for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.prime('nope')
    with pytest.raises(TypeError):
        m.prime(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.prime([('v', 1)] * 101)
    with pytest.raises(TypeError):
        m.prime([('v', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.prime([('v', 1), ('v',)])
    with pytest.raises(TypeError):
        m.prime([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.prime([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.prime([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.prime([('v', '1')])
    with pytest.raises(TypeError):
        m.prime([('v', LyingI())])
    with pytest.raises(TypeError):
        m.prime([('v', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.prime([('v', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.prime([('v', -1)])
    # first bad row pins, mixed failure types
    try:
        m.prime([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.prime([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.prime({'v': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.prime(ListSub([('v', 1)]))
    with pytest.raises(TypeError):
        m.prime([ListSub(('v', 1))])
    # tuple rows accepted exactly like lists
    assert m.prime((('v', 1),)) == m.prime([('v', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.prime([('v', 1), ['v', 2]])
    assert mixed == m.prime([['v', 1], ('v', 2)])
    # boundary acceptance pins
    assert m.prime([('abcdefgh', 1)])['ladders'] == {'abcdefgh': True}
    assert m.prime([('v', 1)] * 100)['total'] == 100
    assert m.prime([('v', 0)])['ladders'] == {'v': True}
    assert m.prime([('v', 10)])['ladders'] == {'v': True}
    # default-start pins: unknown vaccine starts with an unbroken ladder
    r = m.prime([('zz', 1), ('zz', 2)])
    assert r['ladders'] == {'zz': True} and r['laddered'] == ['zz']
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
    ('dose <= previous[vaccine]', 'dose < previous[vaccine]'),
    ('dose <= previous[vaccine]', 'dose <= previous[vaccine] + 1'),
    ('ladders[vaccine] = False', 'ladders[vaccine] = True'),
    ('ladders[vaccine] = True', 'ladders[vaccine] = False'),
    ('if vaccine not in previous:', 'if vaccine in previous:'),
    ('previous[vaccine] = dose', 'previous[vaccine] = dose + 1'),
    ('if ok', 'if not ok'),
    ('laddered = sorted(', 'laddered = list('),
    ('MIN_DOSE = 0', 'MIN_DOSE = 1'),
    ('MAX_DOSE = 10', 'MAX_DOSE = 9'),
    ('not MIN_DOSE <= dose <= MAX_DOSE',
     'not MIN_DOSE < dose < MAX_DOSE'),
    ('vaccine, dose = row', 'dose, vaccine = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(ladders)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(vaccine) <= MAX_NAME',
     'not 1 <= len(vaccine) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'ladders': ladders", "'ladders': previous"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.prime([(S('v'), 5)]), TypeError,
           'row 1: vaccine must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.prime('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.prime(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.prime({'v': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.prime([('v', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.prime([('v', 1), 'bad']), TypeError,
           'row 2: expected (vaccine, dose) tuple, got str')
    _exact(lambda: m.prime([('v', 1), ('v',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.prime([(1, 1)]), TypeError,
           'row 1: vaccine must be str, got int')
    _exact(lambda: m.prime([(True, 1)]), TypeError,
           'row 1: vaccine must be str, got bool')
    _exact(lambda: m.prime([('', 1)]), ValueError,
           'row 1: vaccine must be 1-8 chars')
    _exact(lambda: m.prime([('abcdefghi', 1)]), ValueError,
           'row 1: vaccine must be 1-8 chars')
    _exact(lambda: m.prime([('v', '1')]), TypeError,
           'row 1: dose must be int, got str')
    _exact(lambda: m.prime([('v', True)]), TypeError,
           'row 1: dose must be int, got bool')
    _exact(lambda: m.prime([('v', 11)]), ValueError,
           'row 1: dose must be 0-10, got 11')
    _exact(lambda: m.prime([('v', -1)]), ValueError,
           'row 1: dose must be 0-10, got -1')
    _exact(lambda: m.prime([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: vaccine must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 976, Vaccine Design' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: dose bookkeeping only; no immunology modeled'
    assert module.NOT_CLAIMED == (
        'does not model immune memory',
        'does not weight doses by timing',
        'does not require a minimum record count',
        'does not compare vaccines against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
