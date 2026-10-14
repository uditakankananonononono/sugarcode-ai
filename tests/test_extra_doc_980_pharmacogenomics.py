"""Mutation and oracle tests for extra_doc.pharmacogenomics."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_980_pharmacogenomics.py',
                        'src/sugarcode/extra_doc/pharmacogenomics.py')

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
    # oracle seeded with row number 980
    assert m.panel([]) == {'total': 0, 'signals': {}, 'clear': []}
    # effects 3, 3 cancel to 0 and clear
    r = m.panel([('g', 3), ('g', 3)])
    assert r == {'total': 2, 'signals': {'g': 0}, 'clear': ['g']}
    # 1, 2, 3 cancel to 0 too
    r = m.panel([('g', 1), ('g', 2), ('g', 3)])
    assert r == {'total': 3, 'signals': {'g': 0}, 'clear': ['g']}
    # 3, 5 leave 6
    r = m.panel([('g', 3), ('g', 5)])
    assert r == {'total': 2, 'signals': {'g': 6}, 'clear': []}
    # a lone effect signals itself
    r = m.panel([('g', 7)])
    assert r == {'total': 1, 'signals': {'g': 7}, 'clear': []}
    # cancellation needs matching pairs, so 4, 4, 4 leaves 4
    r = m.panel([('g', 4), ('g', 4), ('g', 4)])
    assert r['signals'] == {'g': 4} and r['clear'] == []
    # the fold is bitwise, not arithmetic: 1, 3 leaves 2
    r = m.panel([('g', 1), ('g', 3)])
    assert r['signals'] == {'g': 2}
    # 6, 3 leaves 5, not 9 or 3
    r = m.panel([('g', 6), ('g', 3)])
    assert r['signals'] == {'g': 5}
    # the order never matters
    r = m.panel([('g', 5), ('g', 3)])
    assert r['signals'] == {'g': 6}
    # each gene keeps its own signal
    r = m.panel([('a', 2), ('b', 2), ('a', 2), ('b', 1)])
    assert r == {'total': 4, 'signals': {'a': 0, 'b': 3}, 'clear': ['a']}
    # boundary effects
    r = m.panel([('g', 10), ('g', 10)])
    assert r['signals'] == {'g': 0} and r['clear'] == ['g']
    r = m.panel([('g', 0)])
    assert r['signals'] == {'g': 0} and r['clear'] == ['g']
    # dynamic equal-string witness: equal genes share one signal
    dyn = ''.join(['g', '1'])
    r = m.panel([(dyn, 6), (''.join(['g', '1']), 6)])
    assert r['signals'] == {'g1': 0} and r['clear'] == ['g1']
    # wide many-name sort pin, inserted in reverse order (20 genes)
    names = ['g%02d' % i for i in range(20)]
    r = m.panel([(n, 5) for n in reversed(names)] + [(n, 5) for n in names])
    assert r['clear'] == sorted(names)
    assert r['signals'] == {n: 0 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.panel('nope')
    with pytest.raises(TypeError):
        m.panel(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.panel([('g', 1)] * 101)
    with pytest.raises(TypeError):
        m.panel([('g', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.panel([('g', 1), ('g',)])
    with pytest.raises(TypeError):
        m.panel([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.panel([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.panel([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.panel([('g', '1')])
    with pytest.raises(TypeError):
        m.panel([('g', LyingI())])
    with pytest.raises(TypeError):
        m.panel([('g', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.panel([('g', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.panel([('g', -1)])
    # first bad row pins, mixed failure types
    try:
        m.panel([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.panel([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.panel({'g': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.panel(ListSub([('g', 1)]))
    with pytest.raises(TypeError):
        m.panel([ListSub(('g', 1))])
    # tuple rows accepted exactly like lists
    assert m.panel((('g', 1),)) == m.panel([('g', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.panel([('g', 3), ['g', 5]])
    assert mixed == m.panel([['g', 3], ('g', 5)])
    # boundary acceptance pins
    assert m.panel([('abcdefgh', 1)])['signals'] == {'abcdefgh': 1}
    assert m.panel([('g', 1)] * 100)['total'] == 100
    assert m.panel([('g', 0)])['signals'] == {'g': 0}
    assert m.panel([('g', 10)])['signals'] == {'g': 10}
    # default-start pins: unknown gene starts from a zero signal
    r = m.panel([('zz', 6), ('zz', 3)])
    assert r['signals'] == {'zz': 5} and r['clear'] == []
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
    ('signals[gene] ^= effect', 'signals[gene] = effect'),
    ('signals[gene] ^= effect', 'signals[gene] += effect'),
    ('signals[gene] ^= effect', 'signals[gene] |= effect'),
    ('signals[gene] ^= effect', 'signals[gene] ^= effect + 1'),
    ('signals[gene] ^= effect', 'signals[gene] ^= effect ^ 1'),
    ('signals[gene] = 0', 'signals[gene] = 1'),
    ('if gene not in signals:', 'if gene in signals:'),
    ('signal == 0', 'signal != 0'),
    ('clear = sorted(', 'clear = list('),
    ('MIN_EFFECT = 0', 'MIN_EFFECT = 1'),
    ('MAX_EFFECT = 10', 'MAX_EFFECT = 9'),
    ('not MIN_EFFECT <= effect <= MAX_EFFECT',
     'not MIN_EFFECT < effect < MAX_EFFECT'),
    ('gene, effect = row', 'effect, gene = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(signals)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(gene) <= MAX_NAME', 'not 1 <= len(gene) < MAX_NAME'),
    ("type(rows) not in (list, tuple)", "type(rows) is not list"),
    ("type(rows) not in (list, tuple)", "isinstance(rows, (list, tuple))"),
    ("type(row) not in (list, tuple)", "type(row) is not list"),
    ("type(row) not in (list, tuple)", "isinstance(row, (list, tuple))"),
    ('len(row) != 2', 'len(row) != 3'),
    ("'signals': signals", "'signals': {g: 0 for g in signals}"),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_dies(old, new):
    assert _survives(old, new) == 'dies'


def test_str_subclass_rejected():
    m = _load_code(SRC)
    _exact(lambda: m.panel([(S('g'), 5)]), TypeError,
           'row 1: gene must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.panel('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.panel(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.panel({'g': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.panel([('g', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.panel([('g', 1), 'bad']), TypeError,
           'row 2: expected (gene, effect) tuple, got str')
    _exact(lambda: m.panel([('g', 1), ('g',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.panel([(1, 1)]), TypeError,
           'row 1: gene must be str, got int')
    _exact(lambda: m.panel([(True, 1)]), TypeError,
           'row 1: gene must be str, got bool')
    _exact(lambda: m.panel([('', 1)]), ValueError,
           'row 1: gene must be 1-8 chars')
    _exact(lambda: m.panel([('abcdefghi', 1)]), ValueError,
           'row 1: gene must be 1-8 chars')
    _exact(lambda: m.panel([('g', '1')]), TypeError,
           'row 1: effect must be int, got str')
    _exact(lambda: m.panel([('g', True)]), TypeError,
           'row 1: effect must be int, got bool')
    _exact(lambda: m.panel([('g', 11)]), ValueError,
           'row 1: effect must be 0-10, got 11')
    _exact(lambda: m.panel([('g', -1)]), ValueError,
           'row 1: effect must be 0-10, got -1')
    _exact(lambda: m.panel([('ok', 1), ('ok', 1), (1, 1)]),
           TypeError, 'row 3: gene must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 980, Pharmacogenomics' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == 'PARTIAL: effect bookkeeping only; no gene-drug mechanism modeled'
    assert module.NOT_CLAIMED == (
        'does not model metabolic pathways',
        'does not weight effects by record order',
        'does not compare genes against each other',
        'does not cap the signal during accumulation',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
