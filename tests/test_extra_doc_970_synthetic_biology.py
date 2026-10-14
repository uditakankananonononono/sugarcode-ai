"""Mutation and oracle tests for extra_doc.synthetic_biology."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_970_synthetic_biology.py',
                        'src/sugarcode/extra_doc/synthetic_biology.py')

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
    # oracle seeded with row number 970
    assert m.assemble([]) == {'total': 0, 'parts': {}, 'clean': []}
    # parts a, b, a give 2 distinct parts and the repeat costs clean
    r = m.assemble([('o', 'a'), ('o', 'b'), ('o', 'a')])
    assert r == {'total': 3, 'parts': {'o': 2}, 'clean': []}
    # parts a, b, c give 3 distinct parts and stay clean
    r = m.assemble([('o', 'a'), ('o', 'b'), ('o', 'c')])
    assert r == {'total': 3, 'parts': {'o': 3}, 'clean': ['o']}
    # one organism's repeat never stains another's build
    r = m.assemble([('o', 'a'), ('p', 'a'), ('o', 'a')])
    assert r == {'total': 3, 'parts': {'o': 1, 'p': 1}, 'clean': ['p']}
    # the same part in two different organisms stains neither
    r = m.assemble([('o', 'a'), ('p', 'a')])
    assert r['parts'] == {'o': 1, 'p': 1} and r['clean'] == ['o', 'p']
    # a repeat noticed on the third use still costs clean
    r = m.assemble([('o', 'a'), ('o', 'b'), ('o', 'c'), ('o', 'a')])
    assert r['parts'] == {'o': 3} and r['clean'] == []
    # dynamic equal-string witness: equal organisms share one build
    dyn = ''.join(['o', '1'])
    r = m.assemble([(dyn, 'a'), (''.join(['o', '1']), 'b')])
    assert r['parts'] == {'o1': 2} and r['clean'] == ['o1']
    # wide many-name sort pin, inserted in reverse order (20 organisms)
    names = ['o%02d' % i for i in range(20)]
    r = m.assemble([(n, 'p') for n in reversed(names)])
    assert r['clean'] == sorted(names)
    assert r['parts'] == {n: 1 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.assemble('nope')
    with pytest.raises(TypeError):
        m.assemble(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.assemble([('o', 'a')] * 101)
    with pytest.raises(TypeError):
        m.assemble([('o', 'a'), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.assemble([('o', 'a'), ('o',)])
    with pytest.raises(TypeError):
        m.assemble([(1, 'a')])
    with pytest.raises(TypeError):
        m.assemble([('o', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.assemble([('', 'a')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.assemble([('o', '')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.assemble([('abcdefghi', 'a')])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.assemble([('o', 'abcdefghi')])
    # organism is validated before the part
    _exact(lambda: m.assemble([(1, 2)]), TypeError,
           'row 1: organism must be str, got int')
    # first bad row pins, mixed failure types
    try:
        m.assemble([('ok', 'a'), ('ok', 'a'), (7, 'a')])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.assemble([('ok', 'a'), ('ok', '')])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.assemble({'o': 'a'})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.assemble(ListSub([('o', 'a')]))
    with pytest.raises(TypeError):
        m.assemble([ListSub(('o', 'a'))])
    # tuple rows accepted exactly like lists
    assert m.assemble((('o', 'a'),)) == m.assemble([('o', 'a')])
    # mixed list/tuple row containers, both orders
    mixed = m.assemble([('o', 'a'), ['o', 'b']])
    assert mixed == m.assemble([['o', 'a'], ('o', 'b')])
    # boundary acceptance pins
    assert m.assemble([('abcdefgh', 'abcdefgh')])['parts'] == {'abcdefgh': 1}
    assert m.assemble([('o', 'a')] * 100)['total'] == 100
    # default-start pins: unknown organism starts with an empty build
    r = m.assemble([('zz', 'a'), ('zz', 'b')])
    assert r['parts'] == {'zz': 2} and r['clean'] == ['zz']
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
    ('if part in seen[organism]:', 'if part not in seen[organism]:'),
    ('dirty.add(organism)', 'dirty.add(part)'),
    ('seen[organism].add(part)', 'seen[organism].discard(part)'),
    ('seen[organism] = set()', 'seen[organism] = set(part)'),
    ('organism not in dirty', 'organism in dirty'),
    ('clean = sorted(', 'clean = list('),
    ('len(seen[organism])', 'len(seen)'),
    ('organism, part = row', 'part, organism = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(seen)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(organism) <= MAX_NAME',
     'not 1 <= len(organism) < MAX_NAME'),
    ('not 1 <= len(part) <= MAX_NAME',
     'not 1 <= len(part) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ('seen[organism].add(part)', 'seen[organism].add(organism)'),
    ('if organism not in seen:', 'if organism in seen:'),
    ("'parts': parts", "'parts': seen"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.assemble([(S('o'), 'a')]), TypeError,
           'row 1: organism must be str, got S')
    _exact(lambda: m.assemble([('o', S('a'))]), TypeError,
           'row 1: part must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.assemble('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.assemble(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.assemble({'o': 'a'}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.assemble([('o', 'a')] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.assemble([('o', 'a'), 'bad']), TypeError,
           'row 2: expected (organism, part) tuple, got str')
    _exact(lambda: m.assemble([('o', 'a'), ('o',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.assemble([(1, 'a')]), TypeError,
           'row 1: organism must be str, got int')
    _exact(lambda: m.assemble([(True, 'a')]), TypeError,
           'row 1: organism must be str, got bool')
    _exact(lambda: m.assemble([('o', 1)]), TypeError,
           'row 1: part must be str, got int')
    _exact(lambda: m.assemble([('', 'a')]), ValueError,
           'row 1: organism must be 1-8 chars')
    _exact(lambda: m.assemble([('abcdefghi', 'a')]), ValueError,
           'row 1: organism must be 1-8 chars')
    _exact(lambda: m.assemble([('o', '')]), ValueError,
           'row 1: part must be 1-8 chars')
    _exact(lambda: m.assemble([('o', 'abcdefghi')]), ValueError,
           'row 1: part must be 1-8 chars')
    _exact(lambda: m.assemble([('ok', 'a'), ('ok', 'a'), (1, 'a')]),
           TypeError, 'row 3: organism must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 970, Synthetic Biology' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: part tallying only; no sequence biology modeled'
    assert module.NOT_CLAIMED == (
        'does not model part compatibility',
        'does not order the parts within a build',
        'does not score build quality beyond repeats',
        'does not compare organisms against each other',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
