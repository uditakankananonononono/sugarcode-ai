"""Mutation and oracle tests for extra_doc.molecular_nanotechnology."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_951_molecular_nanotechnology.py',
                        'src/sugarcode/extra_doc/molecular_nanotechnology.py')

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
    # oracle seeded with row number 951
    assert m.assemble([]) == {'total': 0, 'assembled': True, 'pairs': {},
                              'loose': []}
    # one odd tally blocks assembly
    r = m.assemble([('a', 5), ('b', 4)])
    assert r == {'total': 2, 'assembled': False,
                 'pairs': {'a': 2, 'b': 2}, 'loose': ['a']}
    # tallies aggregate before pairing: two odd rows pair up
    r = m.assemble([('a', 3), ('a', 3)])
    assert r == {'total': 2, 'assembled': True, 'pairs': {'a': 3},
                 'loose': []}
    # even tallies across types assemble
    r = m.assemble([('a', 4), ('a', 2), ('b', 10)])
    assert r['assembled'] is True and r['pairs'] == {'a': 3, 'b': 5}
    # floor pairing: 7 atoms make 3 pairs, not 4
    r = m.assemble([('a', 7)])
    assert r['pairs'] == {'a': 3} and r['loose'] == ['a']
    # a supplied zero is tallied and stays paired
    r = m.assemble([('a', 0)])
    assert r['pairs'] == {'a': 0} and r['assembled'] is True
    # several loose types listed sorted
    r = m.assemble([('c', 1), ('a', 1), ('b', 2)])
    assert r['loose'] == ['a', 'c'] and r['assembled'] is False
    # dynamic equal-string witness: equal atoms share one tally
    dyn = ''.join(['h', '1'])
    r = m.assemble([(dyn, 3), (''.join(['h', '1']), 3)])
    assert r['pairs'] == {'h1': 3} and r['assembled'] is True
    # wide many-name sort pin (20 types, all even)
    names = ['at%02d' % i for i in range(20)]
    r = m.assemble([(n, 2) for n in names])
    assert r['assembled'] is True and r['pairs'] == {n: 1 for n in names}
    assert r['loose'] == []
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.assemble('nope')
    with pytest.raises(TypeError):
        m.assemble(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.assemble([('a', 2)] * 101)
    with pytest.raises(TypeError):
        m.assemble([('a', 2), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.assemble([('a', 2), ('a',)])
    with pytest.raises(TypeError):
        m.assemble([(1, 2)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.assemble([('', 2)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.assemble([('abcdefghi', 2)])
    with pytest.raises(TypeError):
        m.assemble([('a', '2')])
    with pytest.raises(TypeError):
        m.assemble([('a', LyingI())])
    with pytest.raises(TypeError):
        m.assemble([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.assemble([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.assemble([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.assemble([('ok', 2), ('ok', 2), (7, 2)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.assemble([('ok', 2), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.assemble({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.assemble(ListSub([('a', 2)]))
    with pytest.raises(TypeError):
        m.assemble([ListSub(('a', 2))])
    # tuple rows accepted exactly like lists
    assert m.assemble((('a', 2),)) == m.assemble([('a', 2)])
    # boundary acceptance pins
    assert m.assemble([('abcdefgh', 2)])['assembled'] is True
    assert m.assemble([('a', 2)] * 100)['total'] == 100
    assert m.assemble([('a', 0)])['pairs'] == {'a': 0}
    assert m.assemble([('a', 10)])['pairs'] == {'a': 5}
    # default-start pin: unknown atom must start at 0
    r = m.assemble([('zz', 3), ('zz', 3)])
    assert r['pairs'] == {'zz': 3} and r['assembled'] is True
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
    ('count % BOND != 0', 'count % BOND == 0'),
    ('count % BOND != 0', 'count % BOND != 1'),
    ('count % BOND != 0', 'count % 3 != 0'),
    ("'assembled': not loose", "'assembled': bool(loose)"),
    ('count // BOND', 'count // BOND + 1'),
    ('count // BOND', '-(-count // BOND)'),
    ('BOND = 2', 'BOND = 3'),
    ('tally.get(atom, 0) + atoms', 'tally.get(atom, 0) - atoms'),
    ('tally.get(atom, 0)', 'tally.get(atom, 1)'),
    ("'total': len(rows)", "'total': len(tally)"),
    ('atom, atoms = row', 'atoms, atom = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ('MIN_ATOMS = 0', 'MIN_ATOMS = 1'),
    ('MAX_ATOMS = 10', 'MAX_ATOMS = 9'),
    ('not MIN_ATOMS <= atoms <= MAX_ATOMS', 'not MIN_ATOMS < atoms < MAX_ATOMS'),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(atom) <= MAX_NAME', 'not 1 <= len(atom) < MAX_NAME'),
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
    assert 'Row 951, Molecular Nanotechnology' in module.__doc__


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
    _exact(lambda: m.assemble([(S('a'), 2)]), TypeError,
           'row 1: atom must be str, got S')


def test_error_messages_exact_v2():
    m = _load_code(SRC)
    _exact(lambda: m.assemble('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.assemble(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.assemble({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.assemble([('a', 2)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.assemble([('a', 2), 'bad']), TypeError,
           'row 2: expected (atom, atoms) tuple, got str')
    _exact(lambda: m.assemble([('a', 2), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.assemble([(1, 2)]), TypeError,
           'row 1: atom must be str, got int')
    _exact(lambda: m.assemble([(True, 2)]), TypeError,
           'row 1: atom must be str, got bool')
    _exact(lambda: m.assemble([('', 2)]), ValueError,
           'row 1: atom must be 1-8 chars')
    _exact(lambda: m.assemble([('abcdefghi', 2)]), ValueError,
           'row 1: atom must be 1-8 chars')
    _exact(lambda: m.assemble([('a', '2')]), TypeError,
           'row 1: atoms must be int, got str')
    _exact(lambda: m.assemble([('a', True)]), TypeError,
           'row 1: atoms must be int, got bool')
    _exact(lambda: m.assemble([('a', 11)]), ValueError,
           'row 1: atoms must be 0-10, got 11')
    _exact(lambda: m.assemble([('a', -1)]), ValueError,
           'row 1: atoms must be 0-10, got -1')
    _exact(lambda: m.assemble([('a', 2), ('a', 2), (1, 2)]),
           TypeError, 'row 3: atom must be str, got int')


def test_scope_wording_exact_v2():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: stoichiometric tally only; '
                            'no positional chemistry modeled')
    assert module.NOT_CLAIMED == (
        'does not model atomic positions or lattice geometry',
        'does not simulate reaction energies',
        'does not plan assembly sequences',
        'does not model bond types beyond pairing',
    )
