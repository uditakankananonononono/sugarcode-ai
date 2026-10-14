"""Mutation and oracle tests for extra_doc.prime_editing."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_968_prime_editing.py',
                        'src/sugarcode/extra_doc/prime_editing.py')

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
    # oracle seeded with row number 968
    assert m.rewrite([]) == {'total': 0, 'longest': {}, 'viable': []}
    # template 9 with primer 7 extends 16: not viable
    r = m.rewrite([('a', 9, 7)])
    assert r == {'total': 1, 'longest': {'a': 16}, 'viable': []}
    # template 10 with primer 5 extends exactly 15: viable
    r = m.rewrite([('a', 10, 5)])
    assert r == {'total': 1, 'longest': {'a': 15}, 'viable': ['a']}
    # the extension is the per-record sum, not the parts alone:
    # neither 9 nor 7 alone breaks the limit
    r = m.rewrite([('a', 9, 2), ('a', 3, 7)])
    assert r['longest'] == {'a': 11} and r['viable'] == ['a']
    # the longest is kept, not the latest
    r = m.rewrite([('a', 9, 7), ('a', 1, 1)])
    assert r['longest'] == {'a': 16} and r['viable'] == []
    # a short record after a viable one keeps the longest
    r = m.rewrite([('a', 10, 5), ('a', 0, 0)])
    assert r['longest'] == {'a': 15}
    # boundary parts
    r = m.rewrite([('a', 0, 0)])
    assert r['longest'] == {'a': 0} and r['viable'] == ['a']
    r = m.rewrite([('a', 10, 10)])
    assert r['longest'] == {'a': 20} and r['viable'] == []
    # editors are tracked independently
    r = m.rewrite([('a', 1, 1), ('b', 9, 9), ('a', 2, 2)])
    assert r['longest'] == {'a': 4, 'b': 18}
    assert r['viable'] == ['a']
    # dynamic equal-string witness: equal editors share one track
    dyn = ''.join(['b', '1'])
    r = m.rewrite([(dyn, 9, 7), (''.join(['b', '1']), 1, 1)])
    assert r['longest'] == {'b1': 16} and r['viable'] == []
    # wide many-name sort pin, inserted in reverse order (20 editors)
    names = ['ed%02d' % i for i in range(20)]
    r = m.rewrite([(n, 4, 4) for n in reversed(names)])
    assert r['viable'] == sorted(names)
    assert r['longest'] == {n: 8 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.rewrite('nope')
    with pytest.raises(TypeError):
        m.rewrite(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.rewrite([('a', 1, 1)] * 101)
    with pytest.raises(TypeError):
        m.rewrite([('a', 1, 1), 'bad'])
    with pytest.raises(ValueError, match='3 fields'):
        m.rewrite([('a', 1, 1), ('a', 1)])
    with pytest.raises(TypeError):
        m.rewrite([(1, 1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.rewrite([('', 1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.rewrite([('abcdefghi', 1, 1)])
    with pytest.raises(TypeError):
        m.rewrite([('a', '1', 1)])
    with pytest.raises(TypeError):
        m.rewrite([('a', LyingI(), 1)])
    with pytest.raises(TypeError):
        m.rewrite([('a', True, 1)])
    with pytest.raises(ValueError, match='0-10'):
        m.rewrite([('a', 11, 1)])
    with pytest.raises(ValueError, match='0-10'):
        m.rewrite([('a', 1, 11)])
    # first bad row pins, mixed failure types
    try:
        m.rewrite([('ok', 1, 1), ('ok', 1, 1), (7, 1, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.rewrite([('ok', 1, 1), ('ok', 1, 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.rewrite({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.rewrite(ListSub([('a', 1, 1)]))
    with pytest.raises(TypeError):
        m.rewrite([ListSub(('a', 1, 1))])
    # tuple rows accepted exactly like lists
    assert m.rewrite((('a', 1, 1),)) == m.rewrite([('a', 1, 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.rewrite([('a', 1, 1), ['a', 2, 2]])
    assert mixed == m.rewrite([['a', 1, 1], ('a', 2, 2)])
    # boundary acceptance pins
    assert m.rewrite([('abcdefgh', 1, 1)])['longest'] == {'abcdefgh': 2}
    assert m.rewrite([('a', 1, 1)] * 100)['total'] == 100
    assert m.rewrite([('a', 0, 0)])['longest'] == {'a': 0}
    assert m.rewrite([('a', 10, 10)])['longest'] == {'a': 20}
    # default-start pin: unknown editor must start the longest at 0
    r = m.rewrite([('zz', 0, 0)])
    assert r['longest'] == {'zz': 0}
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
    ('extension = template + primer', 'extension = template - primer'),
    ('extension = template + primer', 'extension = template * primer'),
    ('extension = template + primer', 'extension = template'),
    ('max(longest.get(editor, MIN_PART), extension)',
     'min(longest.get(editor, MIN_PART), extension)'),
    ('longest.get(editor, MIN_PART)', 'longest.get(editor, 1)'),
    ('best <= LIMIT', 'best < LIMIT'),
    ('LIMIT = 15', 'LIMIT = 14'),
    ('LIMIT = 15', 'LIMIT = 16'),
    ('viable = sorted(', 'viable = list('),
    ('MIN_PART = 0', 'MIN_PART = 1'),
    ('MAX_PART = 10', 'MAX_PART = 9'),
    ('not MIN_PART <= value <= MAX_PART',
     'not MIN_PART < value < MAX_PART'),
    ('editor, template, primer = row', 'template, editor, primer = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(longest)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(editor) <= MAX_NAME', 'not 1 <= len(editor) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 3', 'len(row) != 2'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.rewrite([(S('a'), 1, 1)]), TypeError,
           'row 1: editor must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.rewrite('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.rewrite(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.rewrite({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.rewrite([('a', 1, 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.rewrite([('a', 1, 1), 'bad']), TypeError,
           'row 2: expected (editor, template, primer) tuple, got str')
    _exact(lambda: m.rewrite([('a', 1, 1), ('a', 1)]), ValueError,
           'row 2: expected 3 fields, got 2')
    _exact(lambda: m.rewrite([(1, 1, 1)]), TypeError,
           'row 1: editor must be str, got int')
    _exact(lambda: m.rewrite([(True, 1, 1)]), TypeError,
           'row 1: editor must be str, got bool')
    _exact(lambda: m.rewrite([('', 1, 1)]), ValueError,
           'row 1: editor must be 1-8 chars')
    _exact(lambda: m.rewrite([('abcdefghi', 1, 1)]), ValueError,
           'row 1: editor must be 1-8 chars')
    _exact(lambda: m.rewrite([('a', '1', 1)]), TypeError,
           'row 1: template must be int, got str')
    _exact(lambda: m.rewrite([('a', 1, '1')]), TypeError,
           'row 1: primer must be int, got str')
    _exact(lambda: m.rewrite([('a', True, 1)]), TypeError,
           'row 1: template must be int, got bool')
    _exact(lambda: m.rewrite([('a', 11, 1)]), ValueError,
           'row 1: template must be 0-10, got 11')
    _exact(lambda: m.rewrite([('a', 1, -1)]), ValueError,
           'row 1: primer must be 0-10, got -1')
    _exact(lambda: m.rewrite([('a', 1, 1), ('a', 1, 1), (1, 1, 1)]),
           TypeError, 'row 3: editor must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 968, Prime Editing' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: extension bookkeeping only; '
                            'no editing outcome modeled')
    assert module.NOT_CLAIMED == (
        'does not model reverse transcriptase kinetics',
        'does not sum extensions across records',
        'does not limit the template and primer separately',
        'does not model insertion or deletion length',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
