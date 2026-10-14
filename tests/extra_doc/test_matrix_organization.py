import random
import pytest
from sugarcode.extra_doc.matrix_organization import check_members as cm

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(members):
    # written from the stated rule: under 2 managers is unmatrixed; over 3 projects is overloaded
    probs = []
    for i, (_, m, p) in enumerate(members):
        if m < 2:
            probs.append((i, 'unmatrixed'))
        if p > 3:
            probs.append((i, 'overloaded'))
    return {'problems': sorted(probs), 'members': sorted({x for x, _, _ in members}), 'total': len(members)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied matrix numbers against two balance bars. It does not say '
              'functions balance, that 2 managers or 3 projects are the right bars, or that any member works '
              'well. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.matrix_organization as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cm([]) == {'problems': [], 'members': [], 'total': 0}
    assert cm([('a', 2, 3)]) == {'problems': [], 'members': ['a'], 'total': 1}
    assert cm([('a', 1, 3)])['problems'] == [(0, 'unmatrixed')]
    assert cm([('a', 0, 0)])['problems'] == [(0, 'unmatrixed')]
    assert cm([('a', 5, 3)])['problems'] == []
    assert cm([('a', 2, 4)])['problems'] == [(0, 'overloaded')]
    assert cm([('a', 2, 10)])['problems'] == [(0, 'overloaded')]
    assert cm([('a', 1, 4)])['problems'] == [(0, 'overloaded'), (0, 'unmatrixed')]
    assert cm([('a', 1, 4), ('b', 2, 3), ('c', 0, 10)])['problems'] == [
        (0, 'overloaded'), (0, 'unmatrixed'), (2, 'overloaded'), (2, 'unmatrixed')]
    assert cm([('b', 2, 3), ('a', 2, 3)]) == {'problems': [], 'members': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4800 + part)
    seen, clean = set(), 0
    for _ in range(60):
        members = []
        for _ in range(rnd.randint(0, 9)):
            members.append((rnd.choice(('m1', 'm2', 'm3')),
                            rnd.choice((0, 1, 2, 5, rnd.randint(0, 5))),
                            rnd.choice((0, 3, 4, 10, rnd.randint(0, 10)))))
        r = cm(members)
        assert r == oracle(members)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'unmatrixed', 'overloaded'} and clean >= 2


def test_limits_accepted():
    members = [('m%02d' % k, 2, 3) for k in range(40)]
    r = cm(members)
    assert r['total'] == 40 and r['problems'] == []
    cm([('a' * 24, 5, 10)])
    cm([('a', 0, 0)])


def err(exc, msg, members):
    with pytest.raises(exc) as e:
        cm(members)
    assert str(e.value) == msg


PM = 'person must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'members must be an exact list', bad)
    err(V, 'member count must be at most 40', [('m', 2, 3)] * 41)
    for bad in (None, ['m', 2, 3], 'ab', TupleSub(('m', 2, 3)), 5):
        err(T, 'each member must be an exact tuple', [bad])
    for bad in ((), ('m', 2), ('m', 2, 3, 0)):
        err(V, 'each member must have 3 items', [bad])
    for bad in NS:
        err(T, 'person must be an exact string', [(bad, 2, 3)])
    for bad in BAD:
        err(V, PM, [(bad, 2, 3)])
    for bad in NI:
        err(T, 'managers must be an exact integer', [('m', bad, 3)])
        err(T, 'projects must be an exact integer', [('m', 2, bad)])
    for bad in (-1, 6, -100, 10**9):
        err(V, 'managers must be 0 to 5', [('m', bad, 3)])
    for bad in (-1, 11, -100, 10**9):
        err(V, 'projects must be 0 to 10', [('m', 2, bad)])


def _order(err):
    err(T, 'members must be an exact list', 'x')
    err(V, 'member count must be at most 40', [None] * 41)
    err(T, 'each member must be an exact tuple', [None, ('m',)])
    err(V, 'each member must have 3 items', [('m',), None])
    err(T, 'person must be an exact string', [(5, -1, -1)])
    err(V, PM, [('A', -1, -1)])
    err(T, 'managers must be an exact integer', [('m', '0', -1)])
    err(V, 'managers must be 0 to 5', [('m', -1, -1)])
    err(T, 'projects must be an exact integer', [('m', 0, '0')])
    err(V, 'projects must be 0 to 10', [('m', 0, -1)])
    err(T, 'person must be an exact string', [('m', 2, 3), (5, 2, 3)])
    err(T, 'managers must be an exact integer', [('m', 2, 3), ('m', '0', 3)])
    err(T, 'projects must be an exact integer', [('m', 2, 3), ('m', 2, '0')])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,t', _collect(_pins))
def test_pin(exc, msg, t):
    err(exc, msg, t)


@pytest.mark.parametrize('exc,msg,t', _collect(_order))
def test_order(exc, msg, t):
    err(exc, msg, t)
