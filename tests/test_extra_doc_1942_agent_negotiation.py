import pathlib
import random
import signal
import types

import pytest

from sugarcode.extra_doc import agent_negotiation as mod

SRC = pathlib.Path(mod.__file__).read_text()
ROOT = pathlib.Path(mod.__file__).parent

NAMES = ('alpha', 'beta', 'Üser-9!', 'Zoë_2', 'Ω-1', 'q?7', 'B', 'x.y,z')
OF = 'row 1: offer must be a string of 1 to 16 characters'
PA = 'row 1: party must be a string of 1 to 16 characters'
BI = 'row 1: bid must be a nonbool integer between 1 and 9'


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
    assert section == ('strategy modeling, preference elicitation, '
                       'game theory, protocol design, production readiness.')
    assert mod.SCOPE == 'PARTIAL: counter counting over supplied bids'
    assert mod.NOT_CLAIMED == ('strategy modeling', 'preference elicitation',
                               'game theory', 'protocol design',
                               'production readiness')


def _expected(rows):
    own = {}
    counters = {}
    previous = None
    for offer, party, bid in rows:
        if previous is not None and party in own:
            if min(previous, own[party]) < bid < max(previous, own[party]):
                counters[party] = counters.get(party, 0) + 1
        own[party] = bid
        previous = bid
    leader = None
    if counters:
        top = max(counters.values())
        order = list(dict.fromkeys(party for _, party, _ in rows))
        leader = next(p for p in order if counters.get(p) == top)
    return {'total': len(rows), 'counters': counters,
            'turns': sum(counters.values()), 'leader': leader}


def _core(m):
    # fixed pins, oracle seeded with row number 1942
    assert m.count_counters([('o', 'a', 1), ('o', 'b', 9),
                             ('o', 'a', 5)]) == {
        'total': 3, 'counters': {'a': 1}, 'turns': 1, 'leader': 'a'}
    # one row accepted with full expected output
    assert m.count_counters([('o', 'p', 5)]) == {
        'total': 1, 'counters': {}, 'turns': 0, 'leader': None}
    # a repeat bid has no room between the references
    assert m.count_counters([('o', 'a', 1), ('o', 'a', 5)]) == {
        'total': 2, 'counters': {}, 'turns': 0, 'leader': None}
    # the interval is strict on both sides
    assert m.count_counters([('o', 'a', 1), ('o', 'b', 9),
                             ('o', 'a', 1)])['counters'] == {}
    assert m.count_counters([('o', 'a', 1), ('o', 'b', 9),
                             ('o', 'a', 9)])['counters'] == {}
    # outside the interval is no counter
    assert m.count_counters([('o', 'a', 5), ('o', 'b', 6),
                             ('o', 'a', 9)])['counters'] == {}
    # a first-time party never counters
    assert m.count_counters([('o', 'a', 1), ('o', 'b', 9),
                             ('o', 'c', 5)]) == {
        'total': 3, 'counters': {}, 'turns': 0, 'leader': None}
    # a leader tie goes to the first supplied party, not the first counter
    assert m.count_counters([('o', 'a', 9), ('o', 'b', 5), ('o', 'a', 1),
                             ('o', 'b', 3), ('o', 'a', 2)]) == {
        'total': 5, 'counters': {'b': 1, 'a': 1}, 'turns': 2, 'leader': 'a'}
    # a clear leader needs no tie rule
    assert m.count_counters([('o', 'x', 9), ('o', 'y', 1), ('o', 'x', 3),
                             ('o', 'y', 8), ('o', 'x', 5)]) == {
        'total': 5, 'counters': {'x': 2}, 'turns': 2, 'leader': 'x'}
    # non-ASCII parties follow the same rule
    assert m.count_counters([('o', 'Üser-9!', 9), ('o', 'q?7', 1),
                             ('o', 'Üser-9!', 4), ('o', 'q?7', 3)]) == {
        'total': 4, 'counters': {'Üser-9!': 1, 'q?7': 1},
        'turns': 2, 'leader': 'Üser-9!'}
    # the party's own previous bid moves with every row
    assert m.count_counters([('o', 'a', 9), ('o', 'b', 1), ('o', 'a', 5),
                             ('o', 'b', 7), ('o', 'a', 6)]) == {
        'total': 5, 'counters': {'a': 2}, 'turns': 2, 'leader': 'a'}
    # pre-seed pin: fresh accumulators only
    assert m.count_counters([('o', 'a', 2), ('o', 'b', 7),
                             ('o', 'a', 4)]) == {
        'total': 3, 'counters': {'a': 1}, 'turns': 1, 'leader': 'a'}
    rng = random.Random(1942)
    for _ in range(300):
        rows = [(rng.choice(NAMES), rng.choice(NAMES), rng.randint(1, 9))
                for _ in range(rng.randint(1, 60))]
        assert m.count_counters(rows) == _expected(rows)
    return True


def _late(m):
    _raises(TypeError, 'rows must be a list or tuple', m.count_counters, 'ab')
    _raises(TypeError, 'rows must be a list or tuple', m.count_counters, 123)
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_counters, [])
    _raises(ValueError, 'rows must contain between 1 and 60 entries',
            m.count_counters, [('a', 'b', 1)] * 61)
    _raises(TypeError, 'row 2: expected an (offer, party, bid) triple',
            m.count_counters, [('a', 'b', 1), 'bad'])
    _raises(ValueError, 'row 2: expected 3 fields, got 2',
            m.count_counters, [('a', 'b', 1), ('a', 'b')])
    _raises(ValueError, 'row 2: expected 3 fields, got 4',
            m.count_counters, [('a', 'b', 1), ('a', 'b', 1, 1)])
    _raises(ValueError, OF, m.count_counters, [(1, 'b', 1)])
    _raises(ValueError, OF, m.count_counters, [('', 'b', 1)])
    _raises(ValueError, OF, m.count_counters, [('x' * 17, 'b', 1)])
    _raises(ValueError, PA, m.count_counters, [('a', 1, 1)])
    _raises(ValueError, PA, m.count_counters, [('a', '', 1)])
    _raises(ValueError, PA, m.count_counters, [('a', 'x' * 17, 1)])
    _raises(ValueError, BI, m.count_counters, [('a', 'b', '1')])
    _raises(ValueError, BI, m.count_counters, [('a', 'b', 0)])
    _raises(ValueError, BI, m.count_counters, [('a', 'b', 10)])
    _raises(ValueError, BI, m.count_counters, [('a', 'b', True)])
    # first bad row pins
    _raises(ValueError, 'row 3: offer must be a string of 1 to 16 characters',
            m.count_counters, [('a', 'b', 1), ('c', 'd', 1), ('', 'e', 1)])
    _raises(ValueError, 'row 2: bid must be a nonbool integer between 1 and 9',
            m.count_counters, [('a', 'b', 1), ('c', 'd', 0)])
    # offer is validated before party, party before bid
    _raises(ValueError, OF, m.count_counters, [('x' * 17, '', 0)])
    _raises(ValueError, PA, m.count_counters, [('a', '', 0)])
    # validation order: bad container before contents
    _raises(TypeError, 'rows must be a list or tuple', m.count_counters, {'e': 1})
    # tuple rows accepted exactly like lists
    assert m.count_counters((('a', 'b', 1),)) == m.count_counters([('a', 'b', 1)])
    # mixed list/tuple row containers, both orders
    mixed = m.count_counters([('a', 'x', 2), ['b', 'y', 1], ('a', 'y', 3)])
    assert mixed == m.count_counters([['a', 'x', 2], ('b', 'y', 1), ['a', 'y', 3]])
    # boundary acceptance pins
    assert m.count_counters([('a', 'b', 1)] * 60)['total'] == 60
    assert m.count_counters([('a', 'b', 9)])['total'] == 1
    # exact-cap acceptance: 16-char labels in each position and late
    assert m.count_counters([('x' * 16, 'b', 5)])['total'] == 1
    assert m.count_counters([('a', 'y' * 16, 5)])['total'] == 1
    assert m.count_counters([('a', 'b', 5),
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
        _raises(TypeError, P, m.count_counters, K([('a', 'b', 1)]))
        _raises(TypeError,
                'row 1: expected an (offer, party, bid) triple',
                m.count_counters, [K(('a', 'b', 1))])
    _raises(ValueError, OF, m.count_counters, [(S('a'), 'b', 1)])
    _raises(ValueError, PA, m.count_counters, [('a', S('b'), 1)])
    _raises(ValueError, BI, m.count_counters, [('a', 'b', I(1))])
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
    ('type(offer) is not str', 'not isinstance(offer, str)'),
    ('type(party) is not str', 'not isinstance(party, str)'),
    ('type(bid) is not int', 'not isinstance(bid, int)'),
    ('not 1 <= len(offer) <= 16', 'not 1 <= len(offer) <= 17'),
    ('not 1 <= len(party) <= 16', 'not 1 <= len(party) <= 17'),
    ('not 1 <= bid <= 9', 'not 1 <= bid <= 10'),
    ('low < bid < high', 'low <= bid < high'),
    ('low < bid < high', 'low < bid <= high'),
    ('if previous is not None and party in own:', 'if previous is not None:'),
    ('                counters[party] += 1', '                counters[party] += 2'),
    ('                turns += 1', '                turns += 2'),
    ('for party in order:', 'for party in counters:'),
    ('for party in order:', 'for party in sorted(order):'),
    ('        own[party] = bid', '        own[party] = 0'),
    ("'counters': counters", "'counters': {}"),
    ("'turns': turns", "'turns': 0"),
    ("'leader': leader", "'leader': None"),
    ("'total': len(rows)", "'total': len(counters)"),
    ('        offer, party, bid = row',
     '        party, offer, bid = row'),
    ('for i, row in enumerate(rows, 1):', 'for i, row in enumerate(rows):'),
]


@pytest.mark.parametrize('old,new', MUTANTS)
def test_mutant_is_killed(old, new):
    assert not _survives(battery, old, new)


def test_battery_on_real_module():
    assert battery(mod) is True
