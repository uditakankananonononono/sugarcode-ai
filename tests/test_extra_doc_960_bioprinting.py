"""Mutation and oracle tests for extra_doc.bioprinting."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_960_bioprinting.py',
                        'src/sugarcode/extra_doc/bioprinting.py')

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
    # oracle seeded with row number 960
    assert m.extrude([]) == {'total': 0, 'drops': {}, 'layered': [],
                             'tops': {}}
    # 2, 5, 5, 3 drops once: the 3 below the 5
    r = m.extrude([('a', 2), ('a', 5), ('a', 5), ('a', 3)])
    assert r == {'total': 4, 'drops': {'a': 1}, 'layered': [],
                 'tops': {'a': 3}}
    # equal heights never count as a drop
    r = m.extrude([('a', 5), ('a', 5)])
    assert r['drops'] == {'a': 0} and r['layered'] == ['a']
    # a head with one record always layers cleanly
    r = m.extrude([('a', 7)])
    assert r == {'total': 1, 'drops': {'a': 0}, 'layered': ['a'],
                 'tops': {'a': 7}}
    # a drop is measured against the previous record, not the peak:
    # 5, 3, 4 drops once (the 3), the 4 is above the previous 3
    r = m.extrude([('a', 5), ('a', 3), ('a', 4)])
    assert r['drops'] == {'a': 1} and r['tops'] == {'a': 4}
    # successive drops each count
    r = m.extrude([('a', 5), ('a', 3), ('a', 2)])
    assert r['drops'] == {'a': 2}
    # boundary heights
    r = m.extrude([('a', 0), ('a', 10)])
    assert r['drops'] == {'a': 0} and r['tops'] == {'a': 10}
    # heads are tracked independently; layered lists only clean heads
    r = m.extrude([('a', 9), ('b', 1), ('a', 2), ('b', 3), ('c', 4)])
    assert r['drops'] == {'a': 1, 'b': 0, 'c': 0}
    assert r['layered'] == ['b', 'c']
    assert r['tops'] == {'a': 2, 'b': 3, 'c': 4}
    # dynamic equal-string witness: equal heads share one track
    dyn = ''.join(['b', '1'])
    r = m.extrude([(dyn, 5), (''.join(['b', '1']), 3)])
    assert r['drops'] == {'b1': 1} and r['tops'] == {'b1': 3}
    # wide many-name sort pin, inserted in reverse order (20 heads)
    names = ['hd%02d' % i for i in range(20)]
    r = m.extrude([(n, 4) for n in reversed(names)])
    assert r['layered'] == sorted(names)
    assert r['drops'] == {n: 0 for n in names}
    assert r['tops'] == {n: 4 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.extrude('nope')
    with pytest.raises(TypeError):
        m.extrude(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.extrude([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.extrude([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.extrude([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.extrude([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.extrude([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.extrude([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.extrude([('a', '1')])
    with pytest.raises(TypeError):
        m.extrude([('a', LyingI())])
    with pytest.raises(TypeError):
        m.extrude([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.extrude([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.extrude([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.extrude([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.extrude([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.extrude({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.extrude(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.extrude([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.extrude(((('a', 1),))) == m.extrude([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.extrude([('a', 5), ['a', 3]])
    assert mixed == m.extrude([['a', 5], ('a', 3)])
    # boundary acceptance pins
    assert m.extrude([('abcdefgh', 1)])['tops'] == {'abcdefgh': 1}
    assert m.extrude([('a', 1)] * 100)['total'] == 100
    assert m.extrude([('a', 0)])['tops'] == {'a': 0}
    assert m.extrude([('a', 10)])['tops'] == {'a': 10}
    # default-start pin: unknown head must start the drop count at 0
    r = m.extrude([('zz', 0)])
    assert r['drops'] == {'zz': 0} and r['tops'] == {'zz': 0}
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
    ('height < previous[head]', 'height <= previous[head]'),
    ('height < previous[head]', 'height > previous[head]'),
    ('drops.setdefault(head, 0)', 'drops.setdefault(head, 1)'),
    ('if head in previous and height < previous[head]:',
     'if height < previous[head]:'),
    ('previous[head] = height', 'previous[head] = previous.get(head, height)'),
    ('drops[head] += 1', 'drops[head] += 2'),
    ('drops[head] == 0', 'drops[head] != 0'),
    ('MIN_HEIGHT = 0', 'MIN_HEIGHT = 1'),
    ('MAX_HEIGHT = 10', 'MAX_HEIGHT = 9'),
    ('not MIN_HEIGHT <= height <= MAX_HEIGHT',
     'not MIN_HEIGHT < height < MAX_HEIGHT'),
    ('head, height = row', 'height, head = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(drops)"),
    ('layered = sorted(', 'layered = list('),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(head) <= MAX_NAME', 'not 1 <= len(head) < MAX_NAME'),
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
    _exact(lambda: m.extrude([(S('a'), 5)]), TypeError,
           'row 1: head must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.extrude('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.extrude(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.extrude({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.extrude([('a', 5)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.extrude([('a', 5), 'bad']), TypeError,
           'row 2: expected (head, height) tuple, got str')
    _exact(lambda: m.extrude([('a', 5), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.extrude([(1, 5)]), TypeError,
           'row 1: head must be str, got int')
    _exact(lambda: m.extrude([(True, 5)]), TypeError,
           'row 1: head must be str, got bool')
    _exact(lambda: m.extrude([('', 5)]), ValueError,
           'row 1: head must be 1-8 chars')
    _exact(lambda: m.extrude([('abcdefghi', 5)]), ValueError,
           'row 1: head must be 1-8 chars')
    _exact(lambda: m.extrude([('a', '5')]), TypeError,
           'row 1: height must be int, got str')
    _exact(lambda: m.extrude([('a', True)]), TypeError,
           'row 1: height must be int, got bool')
    _exact(lambda: m.extrude([('a', 11)]), ValueError,
           'row 1: height must be 0-10, got 11')
    _exact(lambda: m.extrude([('a', -1)]), ValueError,
           'row 1: height must be 0-10, got -1')
    _exact(lambda: m.extrude([('a', 5), ('a', 5), (1, 5)]),
           TypeError, 'row 3: head must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 960, Bioprinting' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: layer-order bookkeeping only; '
                            'no tissue biology modeled')
    assert module.NOT_CLAIMED == (
        'does not model cell viability',
        'does not simulate bioink rheology',
        'does not plan print paths',
        'does not compare a layer to anything but the previous layer',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
