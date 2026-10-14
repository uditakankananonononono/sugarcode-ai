"""Mutation and oracle tests for extra_doc.phage_therapy."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_983_phage_therapy.py',
                        'src/sugarcode/extra_doc/phage_therapy.py')

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
    # oracle seeded with row number 983
    assert m.hunt([]) == {'total': 0, 'crests': {}, 'rugged': []}
    # titers 1, 3, 1 give one crest at the middle record
    r = m.hunt([('p', 1), ('p', 3), ('p', 1)])
    assert r == {'total': 3, 'crests': {'p': 1}, 'rugged': []}
    # 1, 3, 1, 3, 1 give two and read rugged
    r = m.hunt([('p', 1), ('p', 3), ('p', 1), ('p', 3), ('p', 1)])
    assert r == {'total': 5, 'crests': {'p': 2}, 'rugged': ['p']}
    # 3, 3, 1 give none because a crest must be strict
    r = m.hunt([('p', 3), ('p', 3), ('p', 1)])
    assert r['crests'] == {'p': 0} and r['rugged'] == []
    # 1, 3, 3 give none because the next record must drop below it
    r = m.hunt([('p', 1), ('p', 3), ('p', 3)])
    assert r['crests'] == {'p': 0} and r['rugged'] == []
    # 1, 2, 3 give none because the rise never turns
    r = m.hunt([('p', 1), ('p', 2), ('p', 3)])
    assert r['crests'] == {'p': 0}
    # a lone record gives none
    r = m.hunt([('p', 9)])
    assert r == {'total': 1, 'crests': {'p': 0}, 'rugged': []}
    # three crests are rugged too
    r = m.hunt([('p', 1), ('p', 3), ('p', 1), ('p', 3), ('p', 1),
                ('p', 3), ('p', 1)])
    assert r['crests'] == {'p': 3} and r['rugged'] == ['p']
    # a dip that never rises again adds no crest
    r = m.hunt([('p', 5), ('p', 1), ('p', 2)])
    assert r['crests'] == {'p': 0}
    # another phage's records are not neighbors
    r = m.hunt([('a', 1), ('b', 9), ('a', 3), ('b', 1), ('a', 1)])
    assert r == {'total': 5, 'crests': {'a': 1, 'b': 0}, 'rugged': []}
    # boundary titers
    r = m.hunt([('p', 0), ('p', 10), ('p', 0)])
    assert r['crests'] == {'p': 1}
    # dynamic equal-string witness: equal phages share one sequence
    dyn = ''.join(['p', '1'])
    r = m.hunt([(dyn, 1), (''.join(['p', '1']), 3),
                (''.join(['p', '1']), 1)])
    assert r['crests'] == {'p1': 1} and r['rugged'] == []
    # wide many-name sort pin, inserted in reverse order (20 phages)
    names = ['p%02d' % i for i in range(20)]
    rows = []
    for n in reversed(names):
        rows += [(n, 1), (n, 3), (n, 1), (n, 3), (n, 1)]
    r = m.hunt(rows)
    assert r['rugged'] == sorted(names)
    assert r['crests'] == {n: 2 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.hunt('nope')
    with pytest.raises(TypeError):
        m.hunt(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.hunt([('p', 1)] * 101)
    with pytest.raises(TypeError):
        m.hunt([('p', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.hunt([('p', 1), ('p',)])
    with pytest.raises(TypeError):
        m.hunt([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.hunt([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.hunt([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.hunt([('p', '1')])
    with pytest.raises(TypeError):
        m.hunt([('p', LyingI())])
    with pytest.raises(TypeError):
        m.hunt([('p', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.hunt([('p', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.hunt([('p', -1)])
    # first bad row pins, mixed failure types
    try:
        m.hunt([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.hunt([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.hunt({'p': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.hunt(ListSub([('p', 1)]))
    with pytest.raises(TypeError):
        m.hunt([ListSub(('p', 1))])
    # tuple rows accepted exactly like lists
    assert m.hunt((('p', 1),)) == m.hunt([('p', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.hunt([('p', 1), ['p', 3], ('p', 1)])
    assert mixed == m.hunt([['p', 1], ('p', 3), ['p', 1]])
    # boundary acceptance pins
    assert m.hunt([('abcdefgh', 1)])['crests'] == {'abcdefgh': 0}
    assert m.hunt([('p', 1)] * 100)['total'] == 100
    assert m.hunt([('p', 0)])['crests'] == {'p': 0}
    assert m.hunt([('p', 10)])['crests'] == {'p': 0}
    # default-start pins: unknown phage starts with no crests
    r = m.hunt([('zz', 1), ('zz', 3), ('zz', 1), ('zz', 3), ('zz', 1)])
    assert r['crests'] == {'zz': 2} and r['rugged'] == ['zz']
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
    ('seen[-1] > seen[-2] and seen[-1] > titer',
     'seen[-1] >= seen[-2] and seen[-1] > titer'),
    ('seen[-1] > seen[-2] and seen[-1] > titer',
     'seen[-1] > seen[-2] and seen[-1] >= titer'),
    ('seen[-1] > seen[-2] and seen[-1] > titer',
     'seen[-1] > titer'),
    ('len(seen) >= 2', 'len(seen) > 2'),
    ('crests[phage] += 1', 'crests[phage] += 2'),
    ('crests[phage] = 0', 'crests[phage] = 1'),
    ('if phage not in history:', 'if phage in history:'),
    ('seen.append(titer)', 'seen.append(titer + 1)'),
    ('count >= RUGGED', 'count > RUGGED'),
    ('RUGGED = 2', 'RUGGED = 1'),
    ('RUGGED = 2', 'RUGGED = 3'),
    ('rugged = sorted(', 'rugged = list('),
    ('MIN_TITER = 0', 'MIN_TITER = 1'),
    ('MAX_TITER = 10', 'MAX_TITER = 9'),
    ('not MIN_TITER <= titer <= MAX_TITER',
     'not MIN_TITER < titer < MAX_TITER'),
    ('phage, titer = row', 'titer, phage = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(crests)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(phage) <= MAX_NAME',
     'not 1 <= len(phage) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'crests': crests", "'crests': history"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.hunt([(S('p'), 5)]), TypeError,
           'row 1: phage must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.hunt('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.hunt(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.hunt({'p': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.hunt([('p', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.hunt([('p', 1), 'bad']), TypeError,
           'row 2: expected (phage, titer) tuple, got str')
    _exact(lambda: m.hunt([('p', 1), ('p',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.hunt([(1, 1)]), TypeError,
           'row 1: phage must be str, got int')
    _exact(lambda: m.hunt([(True, 1)]), TypeError,
           'row 1: phage must be str, got bool')
    _exact(lambda: m.hunt([('', 1)]), ValueError,
           'row 1: phage must be 1-8 chars')
    _exact(lambda: m.hunt([('abcdefghi', 1)]), ValueError,
           'row 1: phage must be 1-8 chars')
    _exact(lambda: m.hunt([('p', '1')]), TypeError,
           'row 1: titer must be int, got str')
    _exact(lambda: m.hunt([('p', True)]), TypeError,
           'row 1: titer must be int, got bool')
    _exact(lambda: m.hunt([('p', 11)]), ValueError,
           'row 1: titer must be 0-10, got 11')
    _exact(lambda: m.hunt([('p', -1)]), ValueError,
           'row 1: titer must be 0-10, got -1')
    _exact(lambda: m.hunt([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: phage must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 983, Phage Therapy' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: titer bookkeeping only; no infection dynamics modeled'
    assert module.NOT_CLAIMED == (
        'does not model bacterial resistance',
        'does not weight titers by record order',
        'does not count edge records as crests',
        'does not compare phages against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
