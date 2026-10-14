import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import ai_policy as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
PO = 'row 1: policy must be a string of 1 to 16 characters'
PI = 'row 1: pillar must be a string of 1 to 16 characters'
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
    assert section == ('pillar weighting, stakeholder mapping, '
                       'lobbying analysis, legislative forecasting, '
                       'production readiness.')
    assert mod.SCOPE == 'PARTIAL: anchor counting over supplied scores'
    assert mod.NOT_CLAIMED == ('pillar weighting', 'stakeholder mapping',
                               'lobbying analysis',
                               'legislative forecasting',
                               'production readiness')


def _expected(rows):
    holders = {}
    for policy, pillar, _score in rows:
        holders.setdefault(pillar, set()).add(policy)
    anchors = {}
    shared = []
    for pillar, ps in holders.items():
        if len(ps) == 1:
            p = next(iter(ps))
            anchors[p] = anchors.get(p, 0) + 1
        else:
            shared.append(pillar)
    leader = None
    if anchors:
        most = max(anchors.values())
        supply = list(dict.fromkeys(p for p, _pi, _s in rows))
        leader = next(p for p in supply if anchors.get(p) == most)
    return {'total': len(rows), 'anchors': anchors,
            'count': sum(anchors.values()),
            'shared': sorted(shared), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1956
    assert m.count_anchors([('p1', 'x', 5), ('p1', 'y', 5),
                            ('p2', 'y', 5)]) == {
        'total': 3, 'anchors': {'p1': 1}, 'count': 1,
        'shared': ['y'], 'leader': 'p1'}
    # one row accepted with full expected output
    assert m.count_anchors([('p', 'x', 5)]) == {
        'total': 1, 'anchors': {'p': 1}, 'count': 1,
        'shared': [], 'leader': 'p'}
    # a pillar scored by two policies anchors neither
    assert m.count_anchors([('p1', 'x', 5), ('p2', 'x', 9)]) == {
        'total': 2, 'anchors': {}, 'count': 0,
        'shared': ['x'], 'leader': None}
    # repeated rows never multiply an anchor
    assert m.count_anchors([('p', 'x', 5), ('p', 'x', 7)]) == {
        'total': 2, 'anchors': {'p': 1}, 'count': 1,
        'shared': [], 'leader': 'p'}
    # the score never shapes pillar membership
    assert m.count_anchors([('p1', 'x', 1), ('p2', 'y', 9)]) == {
        'total': 2, 'anchors': {'p1': 1, 'p2': 1}, 'count': 2,
        'shared': [], 'leader': 'p1'}
    # shared pillars come back sorted, not in supply order
    assert m.count_anchors([('p1', 'z2', 5), ('p2', 'z2', 5),
                            ('p1', 'z1', 5), ('p2', 'z1', 5)]) == {
        'total': 4, 'anchors': {}, 'count': 0,
        'shared': ['z1', 'z2'], 'leader': None}
    # non-ASCII policies follow the same rule
    assert m.count_anchors([('pÜ', 'x', 5), ('q?7', 'y', 3)]) == {
        'total': 2, 'anchors': {'pÜ': 1, 'q?7': 1}, 'count': 2,
        'shared': [], 'leader': 'pÜ'}
    # a leader tie goes to the first supplied policy
    assert m.count_anchors([('z', 'x1', 5), ('a', 'x2', 5)]) == {
        'total': 2, 'anchors': {'z': 1, 'a': 1}, 'count': 2,
        'shared': [], 'leader': 'z'}
    # pre-seed pin: fresh accumulators only
    assert m.count_anchors([('m', 'x1', 5), ('n', 'x2', 5),
                            ('m', 'x3', 5)]) == {
        'total': 3, 'anchors': {'m': 2, 'n': 1}, 'count': 3,
        'shared': [], 'leader': 'm'}
    rng = random.Random(1956)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_anchors(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_anchors, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_anchors, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_anchors, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_anchors, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected a (policy, pillar, score) triple',
            m.count_anchors, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_anchors, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_anchors, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, PO, m.count_anchors, [(1, 'b', 1)])
    _raises(ValueError, PO, m.count_anchors, [('', 'b', 1)])
    _raises(ValueError, PO, m.count_anchors, [('x' * 17, 'b', 1)])
    _raises(ValueError, PI, m.count_anchors, [('a', 1, 1)])
    _raises(ValueError, PI, m.count_anchors, [('a', '', 1)])
    _raises(ValueError, PI, m.count_anchors, [('a', 'x' * 17, 1)])
    _raises(ValueError, SC, m.count_anchors, [('a', 'b', '1')])
    _raises(ValueError, SC, m.count_anchors, [('a', 'b', 0)])
    _raises(ValueError, SC, m.count_anchors, [('a', 'b', 10)])
    _raises(ValueError, SC, m.count_anchors, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: policy must be a string of 1 to 16 characters',
            m.count_anchors, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: score must be a nonbool integer between 1 and 9',
            m.count_anchors, [('a', 'b', 1), ('c', 'd', 0)])
    # policy is validated before pillar, pillar before score
    _raises(ValueError, PO, m.count_anchors, [('x' * 17, '', 0)])
    _raises(ValueError, PI, m.count_anchors, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_anchors,
            {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_anchors((('a', 'b', 1),)) == m.count_anchors([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_anchors([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_anchors([['a', 'x', 2], ('b', 'y', 1),
                                     ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_anchors([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_anchors([('a', 'b', 9)])['anchors'] == {'a': 1}
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_anchors([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_anchors([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_anchors([('a', 'b', 5),
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
        _raises(TypeError, P, m.count_anchors, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected a (policy, pillar, score) triple',
                m.count_anchors, [K(('a', 'b', 1))])
    _raises(ValueError, PO, m.count_anchors, [(S('a'), 'b', 1)])
    _raises(ValueError, PI, m.count_anchors, [('a', S('b'), 1)])
    _raises(ValueError, SC, m.count_anchors, [('a', 'b', I(1))])
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
    ('type(pillar) is not str', 'not isinstance(pillar, str)'),
    ('type(score) is not int', 'not isinstance(score, int)'),
    ('not 1 <= len(policy) <= 16', 'not 1 <= len(policy) <= 17'),
    ('not 1 <= len(pillar) <= 16', 'not 1 <= len(pillar) <= 17'),
    ('not 1 <= score <= 9', 'not 1 <= score <= 10'),
    ('if len(holders[pillar]) == 1:', 'if len(holders[pillar]) != 1:'),
    ('anchors[policy] += 1', 'anchors[policy] += 2'),
    ('count += 1', 'count += 2'),
    ('for policy in order:', 'for policy in sorted(order):'),
    ("'shared': sorted(shared)", "'shared': shared"),
    ("'anchors': anchors", "'anchors': {}"),
    ("'count': count", "'count': 0"),
    ("'shared': sorted(shared)", "'shared': []"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(anchors)"),
    ('        policy, pillar, score = row',
     '        pillar, policy, score = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
