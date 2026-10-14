"""Mutation and oracle tests for extra_doc.base_editing."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_967_base_editing.py',
                        'src/sugarcode/extra_doc/base_editing.py')

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
    # oracle seeded with row number 967
    assert m.weight([]) == {'total': 0, 'scores': {}, 'precise': []}
    # changes 5 then 3 score 5*1 + 3*2 = 11
    r = m.weight([('a', 5), ('a', 3)])
    assert r == {'total': 2, 'scores': {'a': 11}, 'precise': ['a']}
    # the order matters: 3 then 5 scores 13
    r = m.weight([('a', 3), ('a', 5)])
    assert r['scores'] == {'a': 13}
    # a lone change scores itself
    r = m.weight([('a', 7)])
    assert r == {'total': 1, 'scores': {'a': 7}, 'precise': ['a']}
    # changes 6 then 7 score exactly 20 and stay precise
    r = m.weight([('a', 6), ('a', 7)])
    assert r['scores'] == {'a': 20} and r['precise'] == ['a']
    # changes 7 then 7 score 21, one past the limit
    r = m.weight([('a', 7), ('a', 7)])
    assert r['scores'] == {'a': 21} and r['precise'] == []
    # one more pushes past the limit
    r = m.weight([('a', 6), ('a', 7), ('a', 1)])
    assert r['scores'] == {'a': 23} and r['precise'] == []
    # the place counter is per editor, not global
    r = m.weight([('a', 5), ('b', 5), ('a', 5)])
    assert r['scores'] == {'a': 15, 'b': 5}
    # zero changes score zero but still take a place
    r = m.weight([('a', 0), ('a', 5)])
    assert r['scores'] == {'a': 10}
    # boundary changes
    r = m.weight([('a', 10)])
    assert r['scores'] == {'a': 10}
    # dynamic equal-string witness: equal editors share one counter
    dyn = ''.join(['b', '1'])
    r = m.weight([(dyn, 5), (''.join(['b', '1']), 5)])
    assert r['scores'] == {'b1': 15}
    # wide many-name sort pin, inserted in reverse order (20 editors)
    names = ['ed%02d' % i for i in range(20)]
    r = m.weight([(n, 4) for n in reversed(names)])
    assert r['precise'] == sorted(names)
    assert r['scores'] == {n: 4 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.weight('nope')
    with pytest.raises(TypeError):
        m.weight(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.weight([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.weight([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.weight([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.weight([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.weight([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.weight([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.weight([('a', '1')])
    with pytest.raises(TypeError):
        m.weight([('a', LyingI())])
    with pytest.raises(TypeError):
        m.weight([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.weight([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.weight([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.weight([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.weight([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.weight({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.weight(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.weight([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.weight((('a', 1),)) == m.weight([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.weight([('a', 5), ['a', 3]])
    assert mixed == m.weight([['a', 5], ('a', 3)])
    # boundary acceptance pins
    assert m.weight([('abcdefgh', 1)])['scores'] == {'abcdefgh': 1}
    assert m.weight([('a', 1)] * 100)['total'] == 100
    assert m.weight([('a', 0)])['scores'] == {'a': 0}
    assert m.weight([('a', 10)])['scores'] == {'a': 10}
    # default-start pins: unknown editor must start both counters at 0
    r = m.weight([('zz', 5), ('zz', 5)])
    assert r['scores'] == {'zz': 15}
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
    ('change * places[editor]', 'change + places[editor]'),
    ('change * places[editor]', 'change'),
    ('places.get(editor, 0) + 1', 'places.get(editor, 0)'),
    ('places.get(editor, 0) + 1', 'places.get(editor, 1) + 1'),
    ('scores.get(editor, 0)', 'scores.get(editor, 1)'),
    ('score <= LIMIT', 'score < LIMIT'),
    ('LIMIT = 20', 'LIMIT = 19'),
    ('LIMIT = 20', 'LIMIT = 21'),
    ('precise = sorted(', 'precise = list('),
    ('MIN_CHANGE = 0', 'MIN_CHANGE = 1'),
    ('MAX_CHANGE = 10', 'MAX_CHANGE = 9'),
    ('not MIN_CHANGE <= change <= MAX_CHANGE',
     'not MIN_CHANGE < change < MAX_CHANGE'),
    ('editor, change = row', 'change, editor = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(scores)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(editor) <= MAX_NAME', 'not 1 <= len(editor) < MAX_NAME'),
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
    _exact(lambda: m.weight([(S('a'), 5)]), TypeError,
           'row 1: editor must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.weight('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.weight(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.weight({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.weight([('a', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.weight([('a', 1), 'bad']), TypeError,
           'row 2: expected (editor, change) tuple, got str')
    _exact(lambda: m.weight([('a', 1), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.weight([(1, 1)]), TypeError,
           'row 1: editor must be str, got int')
    _exact(lambda: m.weight([(True, 1)]), TypeError,
           'row 1: editor must be str, got bool')
    _exact(lambda: m.weight([('', 1)]), ValueError,
           'row 1: editor must be 1-8 chars')
    _exact(lambda: m.weight([('abcdefghi', 1)]), ValueError,
           'row 1: editor must be 1-8 chars')
    _exact(lambda: m.weight([('a', '1')]), TypeError,
           'row 1: change must be int, got str')
    _exact(lambda: m.weight([('a', True)]), TypeError,
           'row 1: change must be int, got bool')
    _exact(lambda: m.weight([('a', 11)]), ValueError,
           'row 1: change must be 0-10, got 11')
    _exact(lambda: m.weight([('a', -1)]), ValueError,
           'row 1: change must be 0-10, got -1')
    _exact(lambda: m.weight([('a', 1), ('a', 1), (1, 1)]),
           TypeError, 'row 3: editor must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 967, Base Editing' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: weighted scoring only; no DNA chemistry modeled'
    assert module.NOT_CLAIMED == (
        'does not model conversion efficiency',
        'does not weight by genomic position',
        'does not cap the score during accumulation',
        'does not compare editors against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
