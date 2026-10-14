"""Mutation and oracle tests for extra_doc.personalized_medicine."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_979_personalized_medicine.py',
                        'src/sugarcode/extra_doc/personalized_medicine.py')

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
    # oracle seeded with row number 979
    assert m.tailor([]) == {'total': 0, 'balances': {}, 'steady': []}
    # responses 4, 1, 2 balance 4 - 1 + 2 = 5 and lose steady
    r = m.tailor([('p', 4), ('p', 1), ('p', 2)])
    assert r == {'total': 3, 'balances': {'p': 5}, 'steady': []}
    # 4, 1 balance 3 and hold the edge of the band
    r = m.tailor([('p', 4), ('p', 1)])
    assert r == {'total': 2, 'balances': {'p': 3}, 'steady': ['p']}
    # 1, 4 balance -3, the other edge
    r = m.tailor([('p', 1), ('p', 4)])
    assert r['balances'] == {'p': -3} and r['steady'] == ['p']
    # a lone record balances itself
    r = m.tailor([('p', 5)])
    assert r == {'total': 1, 'balances': {'p': 5}, 'steady': []}
    # the sign alternates per record: 4, 1, 2, 3 balances 2
    r = m.tailor([('p', 4), ('p', 1), ('p', 2), ('p', 3)])
    assert r['balances'] == {'p': 2} and r['steady'] == ['p']
    # while 3, 2, 1, 4 balances -2
    r = m.tailor([('p', 3), ('p', 2), ('p', 1), ('p', 4)])
    assert r['balances'] == {'p': -2} and r['steady'] == ['p']
    # one past the edge on either side loses steady
    r = m.tailor([('p', 5), ('p', 1)])
    assert r['balances'] == {'p': 4} and r['steady'] == []
    r = m.tailor([('p', 1), ('p', 5)])
    assert r['balances'] == {'p': -4} and r['steady'] == []
    # each patient keeps its own sign and balance
    r = m.tailor([('a', 6), ('b', 1), ('a', 2), ('b', 4)])
    assert r == {'total': 4, 'balances': {'a': 4, 'b': -3},
                 'steady': ['b']}
    # boundary responses
    r = m.tailor([('p', 10), ('p', 0), ('p', 10)])
    assert r['balances'] == {'p': 20} and r['steady'] == []
    # dynamic equal-string witness: equal patients share one balance
    dyn = ''.join(['p', '1'])
    r = m.tailor([(dyn, 5), (''.join(['p', '1']), 3)])
    assert r['balances'] == {'p1': 2} and r['steady'] == ['p1']
    # wide many-name sort pin, inserted in reverse order (20 patients)
    names = ['p%02d' % i for i in range(20)]
    r = m.tailor([(n, 2) for n in reversed(names)])
    assert r['steady'] == sorted(names)
    assert r['balances'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.tailor('nope')
    with pytest.raises(TypeError):
        m.tailor(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.tailor([('p', 1)] * 101)
    with pytest.raises(TypeError):
        m.tailor([('p', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.tailor([('p', 1), ('p',)])
    with pytest.raises(TypeError):
        m.tailor([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.tailor([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.tailor([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.tailor([('p', '1')])
    with pytest.raises(TypeError):
        m.tailor([('p', LyingI())])
    with pytest.raises(TypeError):
        m.tailor([('p', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.tailor([('p', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.tailor([('p', -1)])
    # first bad row pins, mixed failure types
    try:
        m.tailor([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.tailor([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.tailor({'p': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.tailor(ListSub([('p', 1)]))
    with pytest.raises(TypeError):
        m.tailor([ListSub(('p', 1))])
    # tuple rows accepted exactly like lists
    assert m.tailor((('p', 1),)) == m.tailor([('p', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.tailor([('p', 4), ['p', 1]])
    assert mixed == m.tailor([['p', 4], ('p', 1)])
    # boundary acceptance pins
    assert m.tailor([('abcdefgh', 1)])['balances'] == {'abcdefgh': 1}
    assert m.tailor([('p', 1)] * 100)['total'] == 100
    assert m.tailor([('p', 0)])['balances'] == {'p': 0}
    assert m.tailor([('p', 10)])['balances'] == {'p': 10}
    # default-start pins: unknown patient starts balanced at 0, sign +
    r = m.tailor([('zz', 5), ('zz', 3)])
    assert r['balances'] == {'zz': 2} and r['steady'] == ['zz']
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
    ('balances[patient] += signs[patient] * response',
     'balances[patient] += response'),
    ('balances[patient] += signs[patient] * response',
     'balances[patient] += signs[patient] + response'),
    ('signs[patient] = -signs[patient]', 'signs[patient] = signs[patient]'),
    ('signs[patient] = 1', 'signs[patient] = -1'),
    ('balances[patient] = 0', 'balances[patient] = 1'),
    ('if patient not in balances:', 'if patient in balances:'),
    ('-BAND <= balance <= BAND', '-BAND < balance < BAND'),
    ('-BAND <= balance <= BAND', 'BAND <= balance <= BAND'),
    ('BAND = 3', 'BAND = 2'),
    ('BAND = 3', 'BAND = 4'),
    ('steady = sorted(', 'steady = list('),
    ('MIN_RESPONSE = 0', 'MIN_RESPONSE = 1'),
    ('MAX_RESPONSE = 10', 'MAX_RESPONSE = 9'),
    ('not MIN_RESPONSE <= response <= MAX_RESPONSE',
     'not MIN_RESPONSE < response < MAX_RESPONSE'),
    ('patient, response = row', 'response, patient = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(balances)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(patient) <= MAX_NAME',
     'not 1 <= len(patient) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'balances': balances", "'balances': signs"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.tailor([(S('p'), 5)]), TypeError,
           'row 1: patient must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.tailor('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.tailor(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.tailor({'p': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.tailor([('p', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.tailor([('p', 1), 'bad']), TypeError,
           'row 2: expected (patient, response) tuple, got str')
    _exact(lambda: m.tailor([('p', 1), ('p',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.tailor([(1, 1)]), TypeError,
           'row 1: patient must be str, got int')
    _exact(lambda: m.tailor([(True, 1)]), TypeError,
           'row 1: patient must be str, got bool')
    _exact(lambda: m.tailor([('', 1)]), ValueError,
           'row 1: patient must be 1-8 chars')
    _exact(lambda: m.tailor([('abcdefghi', 1)]), ValueError,
           'row 1: patient must be 1-8 chars')
    _exact(lambda: m.tailor([('p', '1')]), TypeError,
           'row 1: response must be int, got str')
    _exact(lambda: m.tailor([('p', True)]), TypeError,
           'row 1: response must be int, got bool')
    _exact(lambda: m.tailor([('p', 11)]), ValueError,
           'row 1: response must be 0-10, got 11')
    _exact(lambda: m.tailor([('p', -1)]), ValueError,
           'row 1: response must be 0-10, got -1')
    _exact(lambda: m.tailor([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: patient must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 979, Personalized Medicine' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: response bookkeeping only; no treatment modeling'
    assert module.NOT_CLAIMED == (
        'does not model drug interactions',
        'does not weight responses by recency',
        'does not compare patients against each other',
        'does not cap the balance during accumulation',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
