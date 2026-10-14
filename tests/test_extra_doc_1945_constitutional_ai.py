import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import constitutional_ai as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PR = 'row 1: principle must be a string of 1 to 16 characters'
CL = 'row 1: clause must be a string of 1 to 16 characters'
SE = 'row 1: severity must be a nonbool integer between 1 and 9'


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
    assert section == ('principle authoring, critique generation, '
                       'value learning, red teaming, production readiness.')
    assert mod.SCOPE == 'PARTIAL: peak auditing over supplied severities'
    assert mod.NOT_CLAIMED == ('principle authoring', 'critique generation',
                               'value learning', 'red teaming',
                               'production readiness')


def _expected(rows):
    peaks = {}
    for principle, clause, severity in rows:
        inner = peaks.setdefault(principle, {})
        inner[clause] = max(inner.get(clause, 0), severity)
    weakest = {}
    for principle, inner in peaks.items():
        low = min(inner.values())
        weakest[principle] = next(c for c in inner if inner[c] == low)
    exposed = None
    if weakest:
        bottom = min(peaks[p][weakest[p]] for p in weakest)
        exposed = next(p for p in weakest if peaks[p][weakest[p]] == bottom)
    return {'total': len(rows), 'peaks': peaks,
            'weakest': weakest, 'exposed': exposed}


def _core(m):
    # fixed pins, oracle seeded with row number 1945
    assert m.audit_principles([('p1', 'c1', 5), ('p1', 'c2', 3),
                               ('p2', 'c1', 7), ('p1', 'c1', 2),
                               ('p2', 'c2', 9)]) == {
        'total': 5,
        'peaks': {'p1': {'c1': 5, 'c2': 3}, 'p2': {'c1': 7, 'c2': 9}},
        'weakest': {'p1': 'c2', 'p2': 'c1'}, 'exposed': 'p1'}
    # one row accepted with full expected output
    assert m.audit_principles([('p', 'c', 5)]) == {
        'total': 1, 'peaks': {'p': {'c': 5}},
        'weakest': {'p': 'c'}, 'exposed': 'p'}
    # the peak only moves upward
    assert m.audit_principles([('p', 'c', 9), ('p', 'c', 1)]) == {
        'total': 2, 'peaks': {'p': {'c': 9}},
        'weakest': {'p': 'c'}, 'exposed': 'p'}
    # the weakest tie goes to the first supplied clause
    assert m.audit_principles([('p', 'z', 4), ('p', 'a', 4)]) == {
        'total': 2, 'peaks': {'p': {'z': 4, 'a': 4}},
        'weakest': {'p': 'z'}, 'exposed': 'p'}
    # the exposed tie goes to the first supplied principle
    r = m.audit_principles([('z', 'c', 2), ('a', 'c', 2)])
    assert r['peaks'] == {'z': {'c': 2}, 'a': {'c': 2}}
    assert r['weakest'] == {'z': 'c', 'a': 'c'} and r['exposed'] == 'z'
    # a higher peak can change which clause is weakest
    assert m.audit_principles([('p', 'c1', 5), ('p', 'c2', 1),
                               ('p', 'c2', 6)]) == {
        'total': 3, 'peaks': {'p': {'c1': 5, 'c2': 6}},
        'weakest': {'p': 'c1'}, 'exposed': 'p'}
    # non-ASCII principles follow the same rule
    r = m.audit_principles([('Üser-9!', 'c', 3), ('q?7', 'c', 8)])
    assert r == {'total': 2, 'peaks': {'Üser-9!': {'c': 3}, 'q?7': {'c': 8}},
                 'weakest': {'Üser-9!': 'c', 'q?7': 'c'}, 'exposed': 'Üser-9!'}
    # pre-seed pin: fresh accumulators only
    assert m.audit_principles([('m', 'c', 1), ('n', 'c', 9),
                               ('m', 'd', 4)]) == {
        'total': 3, 'peaks': {'m': {'c': 1, 'd': 4}, 'n': {'c': 9}},
        'weakest': {'m': 'c', 'n': 'c'}, 'exposed': 'm'}
    rng = random.Random(1945)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.audit_principles(rows) == _expected(rows)
    return True


def _late(m):
    P3 = 'row 2: expected a (principle, clause, severity) triple'
    _raises(TypeError, 'rows must be a list or tuple', m.audit_principles, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.audit_principles, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.audit_principles, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.audit_principles, [('a', 'b', 1)] * 61)
    _raises(TypeError, P3, m.audit_principles, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.audit_principles, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.audit_principles, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PR, m.audit_principles, [(1, 'b', 1)])
    _raises(ValueError, PR, m.audit_principles, [('', 'b', 1)])
    _raises(ValueError, PR, m.audit_principles, [('x' * 17, 'b', 1)])
    _raises(ValueError, CL, m.audit_principles, [('a', 1, 1)])
    _raises(ValueError, CL, m.audit_principles, [('a', '', 1)])
    _raises(ValueError, CL, m.audit_principles, [('a', 'x' * 17, 1)])
    _raises(ValueError, SE, m.audit_principles, [('a', 'b', '1')])
    _raises(ValueError, SE, m.audit_principles, [('a', 'b', 0)])
    _raises(ValueError, SE, m.audit_principles, [('a', 'b', 10)])
    _raises(ValueError, SE, m.audit_principles, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: principle must be a string of 1 to 16 characters',
            m.audit_principles, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: severity must be a nonbool integer between 1 and 9',
            m.audit_principles, [('a', 'b', 1), ('c', 'd', 0)])
    # principle is validated before clause, clause before severity
    _raises(ValueError, PR, m.audit_principles, [('x' * 17, '', 0)])
    _raises(ValueError, CL, m.audit_principles, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.audit_principles, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.audit_principles((('a', 'b', 1),)) == m.audit_principles([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.audit_principles([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.audit_principles([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.audit_principles([('a', 'b', 1)] * 60)['total'] == 60
    assert m.audit_principles([('a', 'b', 9)])['peaks'] == {'a': {'b': 9}}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.audit_principles([('x' * 16, 'b', 5)])['total'] == 1
    assert m.audit_principles([('a', 'y' * 16, 5)])['total'] == 1
    assert m.audit_principles([('a', 'b', 5),
                               ('x' * 16, 'y' * 16, 5)])['total'] == 2
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
        _raises(TypeError, P, m.audit_principles, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (principle, clause, severity) triple',
                m.audit_principles, [K(('a', 'b', 1))])
    _raises(ValueError, PR, m.audit_principles, [(S('a'), 'b', 1)])
    _raises(ValueError, CL, m.audit_principles, [('a', S('b'), 1)])
    _raises(ValueError, SE, m.audit_principles, [('a', 'b', I(1))])
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
    ('type(principle) is not str', 'not isinstance(principle, str)'),
    ('type(clause) is not str', 'not isinstance(clause, str)'),
    ('type(severity) is not int', 'not isinstance(severity, int)'),
    ('not 1 <= len(principle) <= 16', 'not 1 <= len(principle) <= 17'),
    ('not 1 <= len(clause) <= 16', 'not 1 <= len(clause) <= 17'),
    ('not 1 <= severity <= 9', 'not 1 <= severity <= 10'),
    ('severity > peaks[principle][clause]',
     'severity < peaks[principle][clause]'),
    ('peaks[principle][clause] < peaks[principle][chosen]',
     'peaks[principle][clause] <= peaks[principle][chosen]'),
    ("'peaks': peaks", "'peaks': {}"),
    ("'weakest': weakest", "'weakest': {}"),
    ("'exposed': exposed", "'exposed': None"),
    ("'total': len(rows)", "'total': len(peaks)"),
    ('        principle, clause, severity = row',
     '        clause, principle, severity = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
