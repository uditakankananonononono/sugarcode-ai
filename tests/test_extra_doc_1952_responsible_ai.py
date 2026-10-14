import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import responsible_ai as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PO = 'row 1: policy must be a string of 1 to 16 characters'
TE = 'row 1: team must be a string of 1 to 16 characters'
SC = 'row 1: score must be a nonbool integer between 1 and 9'


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
    assert section == ('policy authoring, compliance mapping, '
                       'risk assessment, incident review, production '
                       'readiness.')
    assert mod.SCOPE == 'PARTIAL: debut tracking over supplied scores'
    assert mod.NOT_CLAIMED == ('policy authoring', 'compliance mapping',
                               'risk assessment', 'incident review',
                               'production readiness')


def _expected(rows):
    first = {}
    for policy, team, _score in rows:
        first.setdefault(team, policy)
    debuts = {}
    for team, policy in first.items():
        debuts[policy] = debuts.get(policy, 0) + 1
    favorite = None
    if debuts:
        top = max(debuts.values())
        supply = list(dict.fromkeys(p for p, _t, _s in rows))
        favorite = next(p for p in supply if debuts.get(p) == top)
    solo = sorted(team for team, policy in first.items()
                  if debuts[policy] == 1)
    return {'total': len(rows), 'debuts': debuts,
            'favorite': favorite, 'solo': solo}


def _core(m):
    # fixed pins, oracle seeded with row number 1952
    assert m.track_debuts([('p1', 't1', 5), ('p2', 't2', 3),
                           ('p1', 't3', 4), ('p1', 't1', 9)]) == {
        'total': 4, 'debuts': {'p1': 2, 'p2': 1}, 'favorite': 'p1',
        'solo': ['t2']}
    # one row accepted with full expected output
    assert m.track_debuts([('p', 't', 5)]) == {
        'total': 1, 'debuts': {'p': 1}, 'favorite': 'p', 'solo': ['t']}
    # a re-scored team keeps its first policy
    assert m.track_debuts([('p2', 't1', 5), ('p1', 't1', 9)]) == {
        'total': 2, 'debuts': {'p2': 1}, 'favorite': 'p2',
        'solo': ['t1']}
    # a favorite tie goes to the first supplied policy
    assert m.track_debuts([('p2', 't1', 5), ('p1', 't2', 5)]) == {
        'total': 2, 'debuts': {'p2': 1, 'p1': 1}, 'favorite': 'p2',
        'solo': ['t1', 't2']}
    # solo teams come back sorted, not in supply order
    assert m.track_debuts([('pa', 'tb', 5), ('pb', 'ta', 5)]) == {
        'total': 2, 'debuts': {'pa': 1, 'pb': 1}, 'favorite': 'pa',
        'solo': ['ta', 'tb']}
    # non-ASCII policies and teams follow the same rule
    assert m.track_debuts([('pÜ', 'Üser-9!', 5), ('pX', 'q?7', 3)]) == {
        'total': 2, 'debuts': {'pÜ': 1, 'pX': 1}, 'favorite': 'pÜ',
        'solo': ['q?7', 'Üser-9!']}
    # extra rows from one team never add debuts
    assert m.track_debuts([('p1', 't1', 1), ('p1', 't1', 2),
                           ('p1', 't1', 3)]) == {
        'total': 3, 'debuts': {'p1': 1}, 'favorite': 'p1',
        'solo': ['t1']}
    # a policy whose rows are all re-scores earns no debut
    assert m.track_debuts([('p1', 't1', 5), ('p2', 't1', 9),
                           ('p1', 't2', 3)]) == {
        'total': 3, 'debuts': {'p1': 2}, 'favorite': 'p1', 'solo': []}
    # pre-seed pin: fresh accumulators only
    assert m.track_debuts([('pa', 't1', 5), ('pb', 't2', 5),
                           ('pa', 't3', 5), ('pb', 't4', 5),
                           ('pa', 't5', 5)]) == {
        'total': 5, 'debuts': {'pa': 3, 'pb': 2}, 'favorite': 'pa',
        'solo': []}
    rng = random.Random(1952)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.track_debuts(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.track_debuts, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.track_debuts, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_debuts, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.track_debuts, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (policy, team, score) triple',
            m.track_debuts, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.track_debuts, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.track_debuts, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PO, m.track_debuts, [(1, 'b', 1)])
    _raises(ValueError, PO, m.track_debuts, [('', 'b', 1)])
    _raises(ValueError, PO, m.track_debuts, [('x' * 17, 'b', 1)])
    _raises(ValueError, TE, m.track_debuts, [('a', 1, 1)])
    _raises(ValueError, TE, m.track_debuts, [('a', '', 1)])
    _raises(ValueError, TE, m.track_debuts, [('a', 'x' * 17, 1)])
    _raises(ValueError, SC, m.track_debuts, [('a', 'b', '1')])
    _raises(ValueError, SC, m.track_debuts, [('a', 'b', 0)])
    _raises(ValueError, SC, m.track_debuts, [('a', 'b', 10)])
    _raises(ValueError, SC, m.track_debuts, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: policy must be a string of 1 to 16 characters',
            m.track_debuts, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.track_debuts, [('a', 'b', 1), ('c', 'd', 0)])
    # policy is validated before team, team before score
    _raises(ValueError, PO, m.track_debuts, [('x' * 17, '', 0)])
    _raises(ValueError, TE, m.track_debuts, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.track_debuts,
            {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.track_debuts((('a', 'b', 1),)) == m.track_debuts([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.track_debuts([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.track_debuts([['a', 'x', 2], ('b', 'y', 1),
                                    ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.track_debuts([('a', 'b', 1)] * 60)['total'] == 60
    assert m.track_debuts([('a', 'b', 9)])['debuts'] == {'a': 1}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.track_debuts([('x' * 16, 'b', 5)])['total'] == 1
    assert m.track_debuts([('a', 'y' * 16, 5)])['total'] == 1
    assert m.track_debuts([('a', 'b', 5),
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
        _raises(TypeError, P, m.track_debuts, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (policy, team, score) triple',
                m.track_debuts, [K(('a', 'b', 1))])
    _raises(ValueError, PO, m.track_debuts, [(S('a'), 'b', 1)])
    _raises(ValueError, TE, m.track_debuts, [('a', S('b'), 1)])
    _raises(ValueError, SC, m.track_debuts, [('a', 'b', I(1))])
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
    ('type(policy) is not str', 'not isinstance(policy, str)'),
    ('type(team) is not str', 'not isinstance(team, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(policy) <= 16', 'not 1 <= len(policy) <= 17'),
    ('not 1 <= len(team) <= 16', 'not 1 <= len(team) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('if team not in first:', 'if team in first:'),
    ('if policy not in debuts:', 'if policy in debuts:'),
    ('if policy not in order:', 'if policy in order:'),
    ('debuts[policy] += 1', 'debuts[policy] += 2'),
    ('for policy in order:', 'for policy in sorted(order):'),
    ('debuts[first[team]] == 1', 'debuts[first[team]] >= 1'),
    ("'solo': sorted(solo)", "'solo': solo"),
    ("'debuts': debuts", "'debuts': {}"),
    ("'favorite': favorite", "'favorite': None"),
    ("'solo': sorted(solo)", "'solo': []"),
    ("'total': len(rows)", "'total': len(debuts)"),
    ('        policy, team, score = row',
     '        team, policy, score = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
