"""Mutation and oracle tests for extra_doc.retinal_implants."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_997_retinal_implants.py',
                        'src/sugarcode/extra_doc/retinal_implants.py')

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
    # oracle seeded with row number 997
    assert m.see([]) == {'total': 0, 'ledger': {}, 'even': []}
    # charges 1, 2, 3, 4 balance to 2 and read even
    r = m.see([('p', 1), ('p', 2), ('p', 3), ('p', 4)])
    assert r == {'total': 4, 'ledger': {'p': 2}, 'even': ['p']}
    # 5 balances to -5: a lone odd charge never reads even
    r = m.see([('p', 5)])
    assert r == {'total': 1, 'ledger': {'p': -5}, 'even': []}
    # 2, 2 balance to 4
    r = m.see([('p', 2), ('p', 2)])
    assert r == {'total': 2, 'ledger': {'p': 4}, 'even': ['p']}
    # 1, 3 balance to -4
    r = m.see([('p', 1), ('p', 3)])
    assert r == {'total': 2, 'ledger': {'p': -4}, 'even': []}
    # 0 balances to 0 and does not read even: 0 is an even charge
    r = m.see([('p', 0)])
    assert r == {'total': 1, 'ledger': {'p': 0}, 'even': []}
    # 0, 1 balance to -1
    r = m.see([('p', 0), ('p', 1)])
    assert r == {'total': 2, 'ledger': {'p': -1}, 'even': []}
    # 3, 3, 2 balance to -4
    r = m.see([('p', 3), ('p', 3), ('p', 2)])
    assert r == {'total': 3, 'ledger': {'p': -4}, 'even': []}
    # 6, 1 balance to 5 and read even
    r = m.see([('p', 6), ('p', 1)])
    assert r == {'total': 2, 'ledger': {'p': 5}, 'even': ['p']}
    # boundary charges: 10 balances to 10, 9 balances to -9
    r = m.see([('p', 10)])
    assert r['ledger'] == {'p': 10} and r['even'] == ['p']
    r = m.see([('p', 9)])
    assert r['ledger'] == {'p': -9} and r['even'] == []
    # each pixel keeps its own ledger
    r = m.see([('a', 1), ('b', 2), ('a', 3)])
    assert r == {'total': 3, 'ledger': {'a': -4, 'b': 2},
                 'even': ['b']}
    # dynamic equal-string witness: equal pixels share one ledger
    dyn = ''.join(['p', '1'])
    r = m.see([(dyn, 2), (''.join(['p', '1']), 1)])
    assert r['ledger'] == {'p1': 1} and r['even'] == ['p1']
    # wide many-name sort pin, inserted in reverse order (20 names)
    names = ['p%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 2), (n, 2)]
    r = m.see(rows)
    assert r['even'] == sorted(names)
    assert r['ledger'] == {n: 4 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.see('nope')
    with pytest.raises(TypeError):
        m.see(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.see([('p', 1)] * 101)
    with pytest.raises(TypeError):
        m.see([('p', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.see([('p', 1), ('p',)])
    with pytest.raises(TypeError):
        m.see([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.see([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.see([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.see([('p', '1')])
    with pytest.raises(TypeError):
        m.see([('p', LyingI())])
    with pytest.raises(TypeError):
        m.see([('p', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.see([('p', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.see([('p', -1)])
    # first bad row pins, mixed failure types
    try:
        m.see([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.see([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.see({'p': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.see(ListSub([('p', 1)]))
    with pytest.raises(TypeError):
        m.see([ListSub(('p', 1))])
    # tuple rows accepted exactly like lists
    assert m.see((('p', 1),)) == m.see([('p', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.see([('p', 1), ['p', 2], ('p', 4)])
    assert mixed == m.see([['p', 1], ('p', 2), ['p', 4]])
    # boundary acceptance pins
    assert m.see([('abcdefgh', 1)])['ledger'] == {'abcdefgh': -1}
    assert m.see([('p', 1)] * 100)['total'] == 100
    assert m.see([('p', 0)])['ledger'] == {'p': 0}
    assert m.see([('p', 10)])['ledger'] == {'p': 10}
    # default-start pins: unknown pixel starts with an empty ledger
    r = m.see([('zz', 2)])
    assert r['ledger'] == {'zz': 2} and r['even'] == ['zz']
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
    ('charge % 2 == 0', 'charge % 2 == 1'),
    ('charge % 2', 'charge % 3'),
    ('ledger[pixel] += charge', 'ledger[pixel] -= charge'),
    ('ledger[pixel] -= charge', 'ledger[pixel] += charge'),
    ('ledger.setdefault(pixel, 0)', 'ledger.setdefault(pixel, 1)'),
    ('balance > 0', 'balance >= 0'),
    ('balance > 0', 'balance < 0'),
    ('even = sorted(', 'even = list('),
    ('ledger: dict = {}', "ledger: dict = {'zz': 1}"),
    ('pixel, charge = row', 'charge, pixel = row'),
    ('for index, row in enumerate(rows, 1):',
     'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(ledger)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(pixel) <= MAX_NAME',
     'not 1 <= len(pixel) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('MIN_CHARGE = 0', 'MIN_CHARGE = 1'),
    ('MAX_CHARGE = 10', 'MAX_CHARGE = 9'),
    ('not MIN_CHARGE <= charge <= MAX_CHARGE',
     'not MIN_CHARGE < charge < MAX_CHARGE'),
    ("'ledger': ledger", "'ledger': even"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.see([(S('p'), 5)]), TypeError,
           'row 1: pixel must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.see('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.see(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.see({'p': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.see([('p', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.see([('p', 1), 'bad']), TypeError,
           'row 2: expected (pixel, charge) tuple, got str')
    _exact(lambda: m.see([('p', 1), ('p',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.see([(1, 1)]), TypeError,
           'row 1: pixel must be str, got int')
    _exact(lambda: m.see([(True, 1)]), TypeError,
           'row 1: pixel must be str, got bool')
    _exact(lambda: m.see([('', 1)]), ValueError,
           'row 1: pixel must be 1-8 chars')
    _exact(lambda: m.see([('abcdefghi', 1)]), ValueError,
           'row 1: pixel must be 1-8 chars')
    _exact(lambda: m.see([('p', '1')]), TypeError,
           'row 1: charge must be int, got str')
    _exact(lambda: m.see([('p', True)]), TypeError,
           'row 1: charge must be int, got bool')
    _exact(lambda: m.see([('p', 11)]), ValueError,
           'row 1: charge must be 0-10, got 11')
    _exact(lambda: m.see([('p', -1)]), ValueError,
           'row 1: charge must be 0-10, got -1')
    _exact(lambda: m.see([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: pixel must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 997, Retinal Implants' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: charge bookkeeping only; no retinal tissue modeled'
    assert module.NOT_CLAIMED == (
        'does not model phosphene mapping',
        'does not weight charges by record order',
        'does not treat 0 as odd; it adds nothing as an even charge',
        'does not compare pixels against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
