import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import heritage_studies as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
SI = 'row 1: site must be a string of 1 to 16 characters'
RG = 'row 1: region must be a string of 1 to 16 characters'
CA = 'row 1: care must be a nonbool integer between 1 and 9'


def _load_code(code):
    m = types.ModuleType('mutant')
    exec(code, m.__dict__)
    return m


def _raises(exc, message, fn, *args):
    with pytest.raises(exc) as info:
        fn(*args)
    assert str(info.value) == message


def _survives(battery, old, new):
    doc_end = SRC.index('"""', 3) + 3
    assert SRC.find(old) > doc_end, 'mutation target must be code, not the docstring'
    mutated = SRC.replace(old, new, 1)
    assert mutated != SRC
    code = compile(mutated, 'mutant', 'exec')
    def _timeout(*_):
        raise TimeoutError('mutant did not terminate')
    previous = signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(5)
    try:
        battery(_load_code(code))
    except (Exception, pytest.fail.Exception):
        return False
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)
    return True


def test_scope_and_package_rules():
    assert mod.SCOPE.startswith('PARTIAL')
    assert len(mod.NOT_CLAIMED) >= 4 and 'NOT_CLAIMED' in mod.__doc__
    assert not (ROOT / '__init__.py').exists()


def test_disclaimer_text_exact():
    section = ' '.join(mod.__doc__.split('NOT_CLAIMED:', 1)[1].split())
    assert section == ('restoration practice, funding policy, '
                       'tourism impact, legal protection, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: care gauging over supplied readings'
    assert mod.NOT_CLAIMED == ('restoration practice', 'funding policy',
                               'tourism impact', 'legal protection',
                               'production readiness')


def _expected(rows):
    baseline = {}
    declines = {}
    for site, region, care in rows:
        if site not in baseline:
            baseline[site] = care
            declines[site] = 0
        elif care < baseline[site]:
            declines[site] += 1
    steady = sorted(s for s in declines if declines[s] == 0)
    worst = None
    for site in declines:
        if worst is None or declines[site] > declines[worst]:
            worst = site
    return {'total': len(rows), 'declines': declines,
            'steady': steady, 'worst': worst}


def _core(m):
    # fixed pins, oracle seeded with row number 1921
    assert m.gauge_care([('s1', 'r', 5), ('s1', 'r', 3), ('s1', 'r', 9),
                         ('s2', 'r', 4), ('s1', 'r', 2)]) == {
        'total': 5, 'declines': {'s1': 2, 's2': 0},
        'steady': ['s2'], 'worst': 's1'}
    # a first row sets the baseline and never declines
    assert m.gauge_care([('s', 'r', 5)]) == {
        'total': 1, 'declines': {'s': 0}, 'steady': ['s'], 'worst': 's'}
    # equal care is no decline
    assert m.gauge_care([('s', 'r', 3), ('s', 'r', 3)])['steady'] == ['s']
    # rises above the baseline are not declines either
    assert m.gauge_care([('s', 'r', 1), ('s', 'r', 9)])['declines'] == {'s': 0}
    # every later row can decline at once
    assert m.gauge_care([('s', 'r', 9), ('s', 'r', 1), ('s', 'r', 1)]) == {
        'total': 3, 'declines': {'s': 2}, 'steady': [], 'worst': 's'}
    # the worst tie goes to the first supplied site
    r = m.gauge_care([('p', 'r', 6), ('q', 'r', 6),
                      ('p', 'r', 5), ('q', 'r', 5)])
    assert r['declines'] == {'p': 1, 'q': 1} and r['worst'] == 'p'
    # dicts keep first-touch order
    r = m.gauge_care([('z', 'b', 1), ('a', 'a', 2)])
    assert r['declines'] == {'z': 0, 'a': 0}
    # non-ASCII sites follow the same rule
    r = m.gauge_care([('Üser-9!', 'r', 8), ('q?7', 'r', 9), ('Üser-9!', 'r', 1)])
    assert r == {'total': 3, 'declines': {'Üser-9!': 1, 'q?7': 0},
                 'steady': ['q?7'], 'worst': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.gauge_care([('p', 'r', 6), ('p', 'r', 2),
                         ('q', 'r', 6), ('p', 'r', 1)]) == {
        'total': 4, 'declines': {'p': 2, 'q': 0},
        'steady': ['q'], 'worst': 'p'}
    rng = random.Random(1921)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.gauge_care(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.gauge_care, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.gauge_care, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.gauge_care, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.gauge_care, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (site, region, care) triple',
            m.gauge_care, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.gauge_care, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.gauge_care, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, SI, m.gauge_care, [(1, 'b', 1)])
    _raises(ValueError, SI, m.gauge_care, [('', 'b', 1)])
    _raises(ValueError, SI, m.gauge_care, [('x' * 17, 'b', 1)])
    _raises(ValueError, RG, m.gauge_care, [('a', 1, 1)])
    _raises(ValueError, RG, m.gauge_care, [('a', '', 1)])
    _raises(ValueError, RG, m.gauge_care, [('a', 'x' * 17, 1)])
    _raises(ValueError, CA, m.gauge_care, [('a', 'b', '1')])
    _raises(ValueError, CA, m.gauge_care, [('a', 'b', 0)])
    _raises(ValueError, CA, m.gauge_care, [('a', 'b', 10)])
    _raises(ValueError, CA, m.gauge_care, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: site must be a string of 1 to 16 characters',
            m.gauge_care, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: care must be a nonbool integer between 1 and 9',
            m.gauge_care, [('a', 'b', 1), ('c', 'd', 0)])
    # site is validated before region, region before care
    _raises(ValueError, SI, m.gauge_care, [('x' * 17, '', 0)])
    _raises(ValueError, RG, m.gauge_care, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.gauge_care, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.gauge_care((('a', 'b', 1),)) == m.gauge_care([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.gauge_care([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.gauge_care([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.gauge_care([('a', 'b', 1)] * 60)['total'] == 60
    assert m.gauge_care([('a', 'b', 9)])['declines'] == {'a': 0}
    return True


class L(list):
    pass


class T(tuple):
    pass


class S(str):
    pass


class I(int):
    pass


def _sym(m):
    P = 'rows must be a list or tuple'
    for K in (L, T):
        _raises(TypeError, P, m.gauge_care, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (site, region, care) triple',
                m.gauge_care, [K(('a', 'b', 1))])
    _raises(ValueError, SI, m.gauge_care, [(S('a'), 'b', 1)])
    _raises(ValueError, RG, m.gauge_care, [('a', S('b'), 1)])
    _raises(ValueError, CA, m.gauge_care, [('a', 'b', I(1))])
    return True


def battery(m):
    _core(m)
    _late(m)
    _sym(m)
    return True


MUTANTS = [
    ('type(rows) not in (list, tuple)', 'not isinstance(rows, (list, tuple))'),
    ('not 1 <= len(rows) <= 60', 'not 1 <= len(rows) <= 61'),
    ('not 1 <= len(rows) <= 60', 'not 0 <= len(rows) <= 60'),
    ('type(row) not in (list, tuple)', 'not isinstance(row, (list, tuple))'),
    ('len(row) != 3', 'len(row) != 2'),
    ('type(site) is not str', 'not isinstance(site, str)'),
    ('type(region) is not str', 'not isinstance(region, str)'),
    ('type(care) is not int', 'not isinstance(care, int)'),
    ('not 1 <= len(site) <= 16', 'not 1 <= len(site) <= 17'),
    ('not 1 <= len(region) <= 16', 'not 1 <= len(region) <= 17'),
    ('not 1 <= care <= 9', 'not 1 <= care <= 10'),
    ('        elif care < baseline[site]:', '        elif care > baseline[site]:'),
    ('        elif care < baseline[site]:', '        elif care <= baseline[site]:'),
    ('            declines[site] += 1', '            declines[site] += 2'),
    ('if declines[s] == 0', 'if declines[s] == 1'),
    ('if worst is None or declines[site] > declines[worst]:',
     'if worst is None or declines[site] < declines[worst]:'),
    ("'declines': declines", "'declines': baseline"),
    ("'steady': steady", "'steady': []"),
    ("'worst': worst", "'worst': None"),
    ("'total': len(rows)", "'total': len(declines)"),
    ('        site, region, care = row', '        region, site, care = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True


def test_gap_pin_exact_cap_acceptance():
    # gap sweep: exact-cap 16-char labels accepted in each label
    # position, and on a late row
    assert mod.gauge_care([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.gauge_care([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.gauge_care([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
