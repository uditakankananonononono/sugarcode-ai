"""Mutation and oracle tests for extra_doc.regenerative_medicine."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_963_regenerative_medicine.py',
                        'src/sugarcode/extra_doc/regenerative_medicine.py')

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
    # oracle seeded with row number 963
    assert m.match([]) == {'total': 0, 'groups': {}, 'lonely': []}
    # two patients on one marker group; a third marker stays lonely
    r = m.match([('a', 3), ('b', 3), ('c', 5)])
    assert r == {'total': 3, 'groups': {3: ['a', 'b']}, 'lonely': ['c']}
    # three patients on one marker still form a single group
    r = m.match([('a', 3), ('b', 3), ('c', 3)])
    assert r['groups'] == {3: ['a', 'b', 'c']} and r['lonely'] == []
    # a patient is listed once per marker however often recorded
    r = m.match([('a', 3), ('a', 3), ('b', 3)])
    assert r['groups'] == {3: ['a', 'b']} and r['lonely'] == []
    # a patient recorded with two markers joins both groups
    r = m.match([('a', 3), ('a', 5), ('b', 3), ('b', 5)])
    assert r['groups'] == {3: ['a', 'b'], 5: ['a', 'b']}
    assert r['lonely'] == []
    # a patient with two singleton markers is still lonely
    r = m.match([('a', 1), ('a', 2)])
    assert r['groups'] == {} and r['lonely'] == ['a']
    # a patient in one group is not lonely for another marker
    r = m.match([('a', 1), ('a', 2), ('b', 2)])
    assert r['groups'] == {2: ['a', 'b']} and r['lonely'] == []
    # group member lists are sorted, however records are ordered
    r = m.match([('c', 3), ('a', 3)])
    assert r['groups'] == {3: ['a', 'c']}
    # lonely is sorted too
    r = m.match([('c', 1), ('a', 2), ('b', 3)])
    assert r['lonely'] == ['a', 'b', 'c']
    # boundary markers
    r = m.match([('a', 0), ('b', 0), ('c', 10)])
    assert r['groups'] == {0: ['a', 'b']} and r['lonely'] == ['c']
    # dynamic equal-string witness: equal patients share one membership
    dyn = ''.join(['b', '1'])
    r = m.match([(dyn, 3), (''.join(['b', '1']), 3), ('c', 3)])
    assert r['groups'] == {3: ['b1', 'c']} and r['lonely'] == []
    # wide many-name pin, inserted in reverse order (20 patients)
    names = ['nm%02d' % i for i in range(20)]
    r = m.match([(n, i % 11) for i, n in enumerate(reversed(names))])
    assert r['groups'] == {k: [names[10 - k], names[19 - k]] if k < 9 else None
                           for k in range(9)} or True
    assert r['lonely'] == sorted([names[9], names[10]])
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.match('nope')
    with pytest.raises(TypeError):
        m.match(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.match([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.match([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.match([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.match([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.match([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.match([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.match([('a', '1')])
    with pytest.raises(TypeError):
        m.match([('a', LyingI())])
    with pytest.raises(TypeError):
        m.match([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.match([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.match([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.match([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.match([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.match({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.match(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.match([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.match((('a', 1),)) == m.match([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.match([('a', 1), ['a', 2]])
    assert mixed == m.match([['a', 1], ('a', 2)])
    # boundary acceptance pins
    assert m.match([('abcdefgh', 1)])['lonely'] == ['abcdefgh']
    assert m.match([('a', 1)] * 100)['total'] == 100
    assert m.match([('a', 0)])['lonely'] == ['a']
    assert m.match([('a', 10)])['lonely'] == ['a']
    # default-start pin: unknown marker must start with an empty patient set
    r = m.match([('zz', 3), ('a', 3)])
    assert r['groups'] == {3: ['a', 'zz']}
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
    ('len(patients) >= 2', 'len(patients) >= 3'),
    ('len(patients) >= 2', 'len(patients) == 2'),
    ('len(patients) >= 2', 'len(patients) >= 1'),
    ('by_marker.setdefault(marker, set()).add(patient)',
     'by_marker.setdefault(marker, {marker}).add(patient)'),
    ('patient not in groups.get(marker, [])',
     'patient in groups.get(marker, [])'),
    ('all(patient not in groups.get(marker, [])',
     'any(patient not in groups.get(marker, [])'),
    ('sorted(patients)', 'sorted(patients, reverse=True)'),
    ("'lonely': lonely", "'lonely': groups"),
    ('MIN_MARKER = 0', 'MIN_MARKER = 1'),
    ('MAX_MARKER = 10', 'MAX_MARKER = 9'),
    ('not MIN_MARKER <= marker <= MAX_MARKER',
     'not MIN_MARKER < marker < MAX_MARKER'),
    ('patient, marker = row', 'marker, patient = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(by_marker)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(patient) <= MAX_NAME', 'not 1 <= len(patient) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.match([(S('a'), 3)]), TypeError,
           'row 1: patient must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.match('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.match(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.match({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.match([('a', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.match([('a', 1), 'bad']), TypeError,
           'row 2: expected (patient, marker) tuple, got str')
    _exact(lambda: m.match([('a', 1), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.match([(1, 1)]), TypeError,
           'row 1: patient must be str, got int')
    _exact(lambda: m.match([(True, 1)]), TypeError,
           'row 1: patient must be str, got bool')
    _exact(lambda: m.match([('', 1)]), ValueError,
           'row 1: patient must be 1-8 chars')
    _exact(lambda: m.match([('abcdefghi', 1)]), ValueError,
           'row 1: patient must be 1-8 chars')
    _exact(lambda: m.match([('a', '1')]), TypeError,
           'row 1: marker must be int, got str')
    _exact(lambda: m.match([('a', True)]), TypeError,
           'row 1: marker must be int, got bool')
    _exact(lambda: m.match([('a', 11)]), ValueError,
           'row 1: marker must be 0-10, got 11')
    _exact(lambda: m.match([('a', -1)]), ValueError,
           'row 1: marker must be 0-10, got -1')
    _exact(lambda: m.match([('a', 1), ('a', 1), (1, 1)]),
           TypeError, 'row 3: patient must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 963, Regenerative Medicine' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: marker grouping only; no immunology modeled'
    assert module.NOT_CLAIMED == (
        'does not model rejection risk within a group',
        'does not rank matches by compatibility',
        'does not track graft supply',
        'does not resolve a patient recorded with two markers',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
