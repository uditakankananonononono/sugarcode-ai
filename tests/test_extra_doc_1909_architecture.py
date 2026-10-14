import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import architecture as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
BD = 'row 1: building must be a string of 1 to 16 characters'
ST = 'row 1: style must be a string of 1 to 16 characters'
HT = 'row 1: height must be a nonbool integer between 1 and 9'


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
    assert section == ('structural engineering, urban planning, '
                       'preservation, building codes, production readiness.')
    assert mod.SCOPE == 'PARTIAL: skyline measuring over supplied heights'
    assert mod.NOT_CLAIMED == ('structural engineering', 'urban planning',
                               'preservation', 'building codes',
                               'production readiness')


def _expected(rows):
    marks = {}
    styles = {}
    for building, style, height in rows:
        marks[height] = True
        if style not in styles:
            styles[style] = 0
        styles[style] += 1
    vals = sorted(marks, reverse=True)
    peak = vals[0]
    if len(vals) >= 2:
        runner_up = vals[1]
        chasers = sorted({building for building, style, height in rows
                          if height == runner_up})
    else:
        runner_up = None
        chasers = []
    dominant = None
    if styles:
        top = max(styles.values())
        supply = list(dict.fromkeys(s for _b, s, _h in rows))
        dominant = next(s for s in supply if styles.get(s) == top)
    return {'total': len(rows), 'peak': peak, 'runner_up': runner_up,
            'chasers': chasers, 'styles': styles, 'dominant': dominant}


def _core(m):
    # fixed pins, oracle seeded with row number 1909
    assert m.measure_skyline([('b1', 'goth', 9), ('b2', 'goth', 5),
                              ('b3', 'brut', 5), ('b4', 'brut', 1),
                              ('b5', 'goth', 3)]) == {
        'total': 5, 'peak': 9, 'runner_up': 5, 'chasers': ['b2', 'b3'],
        'styles': {'goth': 3, 'brut': 2}, 'dominant': 'goth'}
    # one row: no runner-up
    assert m.measure_skyline([('b', 's', 5)]) == {
        'total': 1, 'peak': 5, 'runner_up': None, 'chasers': [],
        'styles': {'s': 1}, 'dominant': 's'}
    # one distinct height across rows still has no runner-up
    r = m.measure_skyline([('b1', 's', 5), ('b2', 's', 5)])
    assert r['runner_up'] is None and r['chasers'] == []
    # a repeated peak does not chase itself
    r = m.measure_skyline([('a', 's', 9), ('b', 's', 9), ('c', 's', 8)])
    assert r['peak'] == 9 and r['runner_up'] == 8 and r['chasers'] == ['c']
    # the runner-up can be the lowest height
    r = m.measure_skyline([('b1', 'x', 1), ('b2', 'y', 2)])
    assert r['peak'] == 2 and r['runner_up'] == 1 and r['chasers'] == ['b1']
    # a dominant tie ignores alphabetical order
    r = m.measure_skyline([('b1', 'z', 1), ('b2', 'a', 2)])
    assert r['dominant'] == 'z'
    # the dominant tie goes to the first supplied style
    assert m.measure_skyline([('b1', 'x', 1), ('b2', 'y', 2)])['dominant'] == 'x'
    # dicts keep first-touch order
    r = m.measure_skyline([('z', 's', 1), ('a', 't', 2)])
    assert r['styles'] == {'s': 1, 't': 1}
    # non-ASCII buildings sort by codepoint
    r = m.measure_skyline([('Üser-9!', 'a', 5), ('q?7', 'b', 5), ('c', 'd', 9)])
    assert r == {'total': 3, 'peak': 9, 'runner_up': 5,
                 'chasers': ['q?7', 'Üser-9!'],
                 'styles': {'a': 1, 'b': 1, 'd': 1}, 'dominant': 'a'}
    # pre-seed pin: fresh accumulators only
    assert m.measure_skyline([('p', 'a', 9), ('q', 'a', 7),
                              ('q', 'a', 7), ('r', 'b', 2)]) == {
        'total': 4, 'peak': 9, 'runner_up': 7, 'chasers': ['q'],
        'styles': {'a': 3, 'b': 1}, 'dominant': 'a'}
    rng = random.Random(1909)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.measure_skyline(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.measure_skyline, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.measure_skyline, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.measure_skyline, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.measure_skyline, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (building, style, height) triple',
            m.measure_skyline, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.measure_skyline, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.measure_skyline, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, BD, m.measure_skyline, [(1, 'b', 1)])
    _raises(ValueError, BD, m.measure_skyline, [('', 'b', 1)])
    _raises(ValueError, BD, m.measure_skyline, [('x' * 17, 'b', 1)])
    _raises(ValueError, ST, m.measure_skyline, [('a', 1, 1)])
    _raises(ValueError, ST, m.measure_skyline, [('a', '', 1)])
    _raises(ValueError, ST, m.measure_skyline, [('a', 'x' * 17, 1)])
    _raises(ValueError, HT, m.measure_skyline, [('a', 'b', '1')])
    _raises(ValueError, HT, m.measure_skyline, [('a', 'b', 0)])
    _raises(ValueError, HT, m.measure_skyline, [('a', 'b', 10)])
    _raises(ValueError, HT, m.measure_skyline, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: building must be a string of 1 to 16 characters',
            m.measure_skyline, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: height must be a nonbool integer between 1 and 9',
            m.measure_skyline, [('a', 'b', 1), ('c', 'd', 0)])
    # building is validated before style, style before height
    _raises(ValueError, BD, m.measure_skyline, [('x' * 17, '', 0)])
    _raises(ValueError, ST, m.measure_skyline, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.measure_skyline, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.measure_skyline((('a', 'b', 1),)) == m.measure_skyline([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.measure_skyline([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.measure_skyline([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.measure_skyline([('a', 'b', 1)] * 60)['total'] == 60
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.measure_skyline([('x' * 16, 'b', 5)])['total'] == 1
    assert m.measure_skyline([('a', 'y' * 16, 5)])['total'] == 1
    assert m.measure_skyline([('a', 'b', 5),
                              ('x' * 16, 'y' * 16, 5)])['total'] == 2
    assert m.measure_skyline([('a', 'b', 9)])['peak'] == 9
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
        _raises(TypeError, P, m.measure_skyline, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (building, style, height) triple',
                m.measure_skyline, [K(('a', 'b', 1))])
    _raises(ValueError, BD, m.measure_skyline, [(S('a'), 'b', 1)])
    _raises(ValueError, ST, m.measure_skyline, [('a', S('b'), 1)])
    _raises(ValueError, HT, m.measure_skyline, [('a', 'b', I(1))])
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
    ('type(building) is not str', 'not isinstance(building, str)'),
    ('type(style) is not str', 'not isinstance(style, str)'),
    ('type(height) is not int', 'not isinstance(height, int)'),
    ('not 1 <= len(building) <= 16', 'not 1 <= len(building) <= 17'),
    ('not 1 <= len(style) <= 16', 'not 1 <= len(style) <= 17'),
    ('not 1 <= height <= 9', 'not 1 <= height <= 10'),
    ('        styles[style] += 1', '        styles[style] += 2'),
    ('    vals = sorted(marks, reverse=True)', '    vals = sorted(marks)'),
    ('    if len(vals) >= 2:', '    if len(vals) >= 3:'),
    ('                          if height == runner_up})',
     '                          if height == peak})'),
    ("'runner_up': runner_up", "'runner_up': peak"),
    ("'chasers': chasers", "'chasers': []"),
    ('if dominant is None or styles[style] > styles[dominant]:',
     'if dominant is None or styles[style] < styles[dominant]:'),
    ('    for style in styles:', '    for style in sorted(styles):'),
    ("'styles': styles", "'styles': marks"),
    ("'total': len(rows)", "'total': len(styles)"),
    ('        building, style, height = row',
     '        style, building, height = row'),
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
    assert mod.measure_skyline([('x' * 16, 'b', 5)])['total'] == 1
    assert mod.measure_skyline([('a', 'y' * 16, 5)])['total'] == 1
    assert mod.measure_skyline([('a', 'b', 5), ('x' * 16, 'y' * 16, 5)])['total'] == 2
