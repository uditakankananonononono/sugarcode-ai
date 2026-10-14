"""Mutation and oracle tests for extra_doc.crispr_applications."""

import signal
import types

import pytest

HERE = __file__
SRC_PATH = HERE.replace('tests/test_extra_doc_966_crispr_applications.py',
                        'src/sugarcode/extra_doc/crispr_applications.py')

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
    # oracle seeded with row number 966
    assert m.excise([]) == {'total': 0, 'excisions': {}, 'cutting': []}
    # cuts at 1 and 5 excise one fragment
    r = m.excise([('a', 1), ('a', 5)])
    assert r == {'total': 2, 'excisions': {'a': 1}, 'cutting': ['a']}
    # cuts at 1, 5, 9 excise two: 1-5 and 5-9
    r = m.excise([('a', 1), ('a', 5), ('a', 9)])
    assert r['excisions'] == {'a': 2}
    # a repeated cut counts once: sites are distinct
    r = m.excise([('a', 1), ('a', 5), ('a', 5)])
    assert r['excisions'] == {'a': 1}
    # cuts 3 apart excise nothing
    r = m.excise([('a', 2), ('a', 5)])
    assert r == {'total': 2, 'excisions': {'a': 0}, 'cutting': []}
    # boundary pair 0 and 4 excises; 6 and 10 excises
    assert m.excise([('a', 0), ('a', 4)])['excisions'] == {'a': 1}
    assert m.excise([('a', 6), ('a', 10)])['excisions'] == {'a': 1}
    # a pair would run off the field: 7 and 10 are only 3 apart
    assert m.excise([('a', 7), ('a', 10)])['excisions'] == {'a': 0}
    # only the lower site starts a pair: 5 alone after 1 counts once
    r = m.excise([('a', 5), ('a', 1)])
    assert r['excisions'] == {'a': 1}
    # guides are tracked independently
    r = m.excise([('a', 1), ('b', 2), ('a', 5), ('b', 3)])
    assert r['excisions'] == {'a': 1, 'b': 0}
    assert r['cutting'] == ['a']
    # dynamic equal-string witness: equal guides share one site set
    dyn = ''.join(['b', '1'])
    r = m.excise([(dyn, 1), (''.join(['b', '1']), 5)])
    assert r['excisions'] == {'b1': 1}
    # wide many-name sort pin, inserted in reverse order (20 guides)
    names = ['gd%02d' % i for i in range(20)]
    rows = [(n, site) for n in reversed(names) for site in (0, 4)]
    r = m.excise(rows)
    assert r['cutting'] == sorted(names)
    assert r['excisions'] == {n: 1 for n in names}
    return True


def _late(module):
    m = module
    with pytest.raises(TypeError):
        m.excise('nope')
    with pytest.raises(TypeError):
        m.excise(123)
    with pytest.raises(ValueError, match='at most 100'):
        m.excise([('a', 1)] * 101)
    with pytest.raises(TypeError):
        m.excise([('a', 1), 'bad'])
    with pytest.raises(ValueError, match='2 fields'):
        m.excise([('a', 1), ('a',)])
    with pytest.raises(TypeError):
        m.excise([(1, 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.excise([('', 1)])
    with pytest.raises(ValueError, match='1-8 chars'):
        m.excise([('abcdefghi', 1)])
    with pytest.raises(TypeError):
        m.excise([('a', '1')])
    with pytest.raises(TypeError):
        m.excise([('a', LyingI())])
    with pytest.raises(TypeError):
        m.excise([('a', True)])
    with pytest.raises(ValueError, match='0-10'):
        m.excise([('a', 11)])
    with pytest.raises(ValueError, match='0-10'):
        m.excise([('a', -1)])
    # first bad row pins, mixed failure types
    try:
        m.excise([('ok', 1), ('ok', 1), (7, 1)])
    except TypeError as e:
        assert 'row 3' in str(e)
    else:
        pytest.fail('expected TypeError for row 3')
    try:
        m.excise([('ok', 1), ('ok', 99)])
    except ValueError as e:
        assert 'row 2' in str(e)
    else:
        pytest.fail('expected ValueError for row 2')
    # validation order: bad container before contents
    with pytest.raises(TypeError):
        m.excise({'a': 1})
    # exact containers: subclasses refused
    with pytest.raises(TypeError):
        m.excise(ListSub([('a', 1)]))
    with pytest.raises(TypeError):
        m.excise([ListSub(('a', 1))])
    # tuple rows accepted exactly like lists
    assert m.excise((('a', 1),)) == m.excise([('a', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.excise([('a', 1), ['a', 5]])
    assert mixed == m.excise([['a', 1], ('a', 5)])
    # boundary acceptance pins
    assert m.excise([('abcdefgh', 1)])['excisions'] == {'abcdefgh': 0}
    assert m.excise([('a', 1)] * 100)['total'] == 100
    assert m.excise([('a', 0)])['excisions'] == {'a': 0}
    assert m.excise([('a', 10)])['excisions'] == {'a': 0}
    # default-start pin: unknown guide must start with an empty site set
    assert m.excise([('a', 4)])['excisions'] == {'a': 0}
    r = m.excise([('zz', 1), ('zz', 5)])
    assert r['excisions'] == {'zz': 1}
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
    ('FRAGMENT = 4', 'FRAGMENT = 3'),
    ('FRAGMENT = 4', 'FRAGMENT = 5'),
    ('site + FRAGMENT in cuts', 'site + FRAGMENT + 1 in cuts'),
    ('sum(1 for site in cuts if site + FRAGMENT in cuts)',
     'sum(2 for site in cuts if site + FRAGMENT in cuts)'),
    ('sites.setdefault(guide, set()).add(site)',
     'sites.setdefault(guide, {0}).add(site)'),
    ('count > 0', 'count >= 0'),
    ('count > 0', 'count > 1'),
    ('cutting = sorted(', 'cutting = list('),
    ('MIN_SITE = 0', 'MIN_SITE = 1'),
    ('MAX_SITE = 10', 'MAX_SITE = 9'),
    ('not MIN_SITE <= site <= MAX_SITE',
     'not MIN_SITE < site < MAX_SITE'),
    ('guide, site = row', 'site, guide = row'),
    ('for index, row in enumerate(rows, 1):', 'for index, row in enumerate(rows):'),
    ("'total': len(rows)", "'total': len(sites)"),
    ('MAX_ROWS = 100', 'MAX_ROWS = 99'),
    ('MAX_NAME = 8', 'MAX_NAME = 7'),
    ('not 1 <= len(guide) <= MAX_NAME', 'not 1 <= len(guide) < MAX_NAME'),
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
    _exact(lambda: m.excise([(S('a'), 1)]), TypeError,
           'row 1: guide must be str, got S')


def test_error_messages_exact():
    m = _load_code(SRC)
    _exact(lambda: m.excise('nope'), TypeError,
           'rows must be list or tuple, got str')
    _exact(lambda: m.excise(123), TypeError,
           'rows must be list or tuple, got int')
    _exact(lambda: m.excise({'a': 1}), TypeError,
           'rows must be list or tuple, got dict')
    _exact(lambda: m.excise([('a', 1)] * 101), ValueError,
           'rows must contain at most 100 entries')
    _exact(lambda: m.excise([('a', 1), 'bad']), TypeError,
           'row 2: expected (guide, site) tuple, got str')
    _exact(lambda: m.excise([('a', 1), ('a',)]), ValueError,
           'row 2: expected 2 fields, got 1')
    _exact(lambda: m.excise([(1, 1)]), TypeError,
           'row 1: guide must be str, got int')
    _exact(lambda: m.excise([(True, 1)]), TypeError,
           'row 1: guide must be str, got bool')
    _exact(lambda: m.excise([('', 1)]), ValueError,
           'row 1: guide must be 1-8 chars')
    _exact(lambda: m.excise([('abcdefghi', 1)]), ValueError,
           'row 1: guide must be 1-8 chars')
    _exact(lambda: m.excise([('a', '1')]), TypeError,
           'row 1: site must be int, got str')
    _exact(lambda: m.excise([('a', True)]), TypeError,
           'row 1: site must be int, got bool')
    _exact(lambda: m.excise([('a', 11)]), ValueError,
           'row 1: site must be 0-10, got 11')
    _exact(lambda: m.excise([('a', -1)]), ValueError,
           'row 1: site must be 0-10, got -1')
    _exact(lambda: m.excise([('a', 1), ('a', 1), (1, 1)]),
           TypeError, 'row 3: guide must be str, got int')


def test_module_docstring_and_scope():
    module = _load_code(SRC)
    assert module.SCOPE.startswith('PARTIAL:')
    assert len(module.NOT_CLAIMED) >= 4
    assert 'Row 966, CRISPR Applications' in module.__doc__


def test_scope_wording_exact():
    module = _load_code(SRC)
    assert module.SCOPE == ('PARTIAL: cut-site bookkeeping only; '
                            'no repair outcomes modeled')
    assert module.NOT_CLAIMED == (
        'does not model off-target cutting',
        'does not choose between repair pathways',
        'does not count overlapping fragments more than once per site pair',
        'does not order the cuts in time',
    )


def test_battery_on_source():
    module = _load_code(SRC)
    assert battery(module) is True
