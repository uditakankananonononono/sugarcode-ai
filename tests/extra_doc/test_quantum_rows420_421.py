import random
import pytest
from sugarcode.extra_doc.community_management import check_queue as cq
from sugarcode.extra_doc.influencer_marketing import check_deals as cd

T, V = TypeError, ValueError


class StrSub(str):
    pass


class IntSub(int):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle_q(posts):
    probs, waits = [], []
    for i, (a, b) in enumerate(posts):
        if b is None:
            probs.append((i, 'unanswered'))
            continue
        w = b - a
        if w < 0:
            probs.append((i, 'time_travel'))
            continue
        waits.append(w)
        if w >= 61:
            probs.append((i, 'slow'))
    return {'problems': sorted(probs), 'answered': len(waits), 'waits': sorted(waits),
            'longest': max(waits, default=0)}


def oracle_d(budget, deals):
    probs = []
    for i, (h, f, r) in enumerate(deals):
        if h in [x[0] for x in deals[:i]]:
            probs.append((i, 'same_handle'))
        if f > r / 10:
            probs.append((i, 'pricey'))
    spend = sum(f for _, f, _ in deals)
    return {'problems': sorted(probs), 'gaps': ['over_budget'] * (spend > budget), 'spend': spend,
            'reach': sum(r for *_, r in deals), 'left': budget - spend}


def test_hand_q():
    assert cq([]) == {'problems': [], 'answered': 0, 'waits': [], 'longest': 0}
    r = cq([(10, 70), (10, 71), (10, 9), (10, None), (0, 0)])
    assert r == {'problems': [(1, 'slow'), (2, 'time_travel'), (3, 'unanswered')], 'answered': 3,
                 'waits': [0, 60, 61], 'longest': 61}
    assert cq([(100000, 100000)])['waits'] == [0]


def test_hand_d():
    assert cd(0, []) == {'problems': [], 'gaps': [], 'spend': 0, 'reach': 0, 'left': 0}
    r = cd(100, [('a', 10, 100), ('a', 11, 100), ('b', 50, 1000)])
    assert r['problems'] == [(1, 'pricey'), (1, 'same_handle')]
    assert r['gaps'] == [] and r['spend'] == 71 and r['left'] == 29
    assert cd(71, [('a', 10, 100), ('b', 61, 610)])['gaps'] == []
    assert cd(70, [('a', 10, 100), ('b', 61, 610)])['gaps'] == ['over_budget']
    assert cd(5, [('a', 10, 100)])['left'] == -5
    assert cd(0, [('a', 0, 1)])['problems'] == []


@pytest.mark.parametrize('part', range(4))
def test_random(part):
    rnd = random.Random(42000 + part)
    for _ in range(100):
        ps = [(rnd.choice([0, 10, 500]), rnd.choice([None, 0, 5, 10, 69, 70, 71, 510, 570, 571, 600]))
              for _ in range(rnd.randint(0, 30))]
        assert cq(ps) == oracle_q(ps)
        ds = [(rnd.choice('abcd'), rnd.choice([0, 9, 10, 11, 100]), rnd.choice([1, 99, 100, 101, 110, 1000]))
              for _ in range(rnd.randint(0, 20))]
        b = rnd.choice([0, 50, 300, 1000])
        assert cd(b, ds) == oracle_d(b, ds)


def e(fn, exc, msg, *a):
    with pytest.raises(exc) as x:
        fn(*a)
    assert str(x.value) == msg


def test_pins_q():
    for b in (None, (), ListSub([])):
        e(cq, T, 'posts must be an exact list', b)
    e(cq, V, 'post count must be at most 30', [(0, None)] * 31)
    for b in (None, [0, 1], TupleSub((0, 1))):
        e(cq, T, 'each post must be an exact tuple', [b])
    for b in ((), (0,), (0, 1, 2)):
        e(cq, V, 'each post must have 2 items', [b])
    for b in (None, 1.0, True, IntSub(1)):
        e(cq, T, 'posted must be an exact int', [(b, None)])
    for b in (1.0, True, IntSub(1), '1'):
        e(cq, T, 'replied must be an exact int', [(0, b)])
    for b in (-1, 100001):
        e(cq, V, 'posted must be 0 to 100000', [(b, None)])
        e(cq, V, 'replied must be 0 to 100000', [(0, b)])
    e(cq, T, 'posted must be an exact int', [(0, 1), ('x', 'y')])
    e(cq, V, 'posted must be 0 to 100000', [(-1, 'y')])


def test_pins_d():
    for b in (None, 1.0, True, IntSub(1)):
        e(cd, T, 'budget must be an exact int', b, [])
    for b in (-1, 1000001):
        e(cd, V, 'budget must be 0 to 1000000', b, [])
    for b in (None, (), ListSub([])):
        e(cd, T, 'deals must be an exact list', 0, b)
    e(cd, V, 'deal count must be at most 20', 0, [('a', 0, 1)] * 21)
    for b in (None, ['a', 0, 1], TupleSub(('a', 0, 1))):
        e(cd, T, 'each deal must be an exact tuple', 0, [b])
    for b in ((), ('a', 0), ('a', 0, 1, 2)):
        e(cd, V, 'each deal must have 3 items', 0, [b])
    for b in (None, 5, StrSub('a')):
        e(cd, T, 'handle must be an exact string', 0, [(b, 0, 1)])
    for b in ('', 'A', '1a', 'a' * 25):
        e(cd, V, 'handle must be 1 to 24 lowercase identifier characters', 0, [(b, 0, 1)])
    for b in (None, 1.0, True, IntSub(1)):
        e(cd, T, 'fee must be an exact int', 0, [('a', b, 1)])
        e(cd, T, 'reach must be an exact int', 0, [('a', 0, b)])
    for b in (-1, 1000001):
        e(cd, V, 'fee must be 0 to 1000000', 0, [('a', b, 1)])
    for b in (0, 100000001):
        e(cd, V, 'reach must be 1 to 100000000', 0, [('a', 0, b)])
    e(cd, T, 'handle must be an exact string', 0, [('a', 0, 1), (5, 'x', 'y')])
    e(cd, T, 'fee must be an exact int', 0, [('a', 'x', 'y')])
    cd(1000000, [('a' * 24, 1000000, 100000000)])


BADLABELS = ['_a', 'a-b', 'a b', 'a.b', 'a\n', ' a', 'a ', 'a\x00', '\uff41', 'a1-', 'a/b', '9a']


def test_label_charset_witnesses():
    for b in BADLABELS:
        e(cd, V, 'handle must be 1 to 24 lowercase identifier characters', 0, [(b, 0, 1)])
    for g in ('a_', 'a1', 'z9_', 'a' * 24):
        cd(0, [(g, 0, 1)])


def test_subclass_refusal_everywhere():
    e(cd, T, 'handle must be an exact string', 0, [(StrSub('a'), 0, 1)])
    e(cd, T, 'budget must be an exact int', IntSub(0), [])
    e(cd, T, 'fee must be an exact int', 0, [('a', IntSub(0), 1)])
    e(cd, T, 'reach must be an exact int', 0, [('a', 0, IntSub(1))])
    e(cd, T, 'each deal must be an exact tuple', 0, [TupleSub(('a', 0, 1))])
    e(cd, T, 'deals must be an exact list', 0, ListSub())
    e(cq, T, 'posted must be an exact int', [(IntSub(0), None)])
    e(cq, T, 'replied must be an exact int', [(0, IntSub(0))])
    e(cq, T, 'each post must be an exact tuple', [TupleSub((0, None))])
    e(cq, T, 'posts must be an exact list', ListSub())
