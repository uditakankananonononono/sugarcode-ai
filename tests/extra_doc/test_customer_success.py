import random
import pytest
from sugarcode.extra_doc.customer_success import check_accounts as ca

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(accounts):
    # written from the stated rule: health below 40 is at_risk; healthy but untouched over 30 days is neglected
    probs = []
    for i, (_, h, d) in enumerate(accounts):
        if h < 40:
            probs.append((i, 'at_risk'))
        if h >= 80 and d > 30:
            probs.append((i, 'neglected_win'))
    return {'problems': sorted(probs), 'accounts': sorted({a for a, _, _ in accounts}), 'total': len(accounts)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied health scores against two attention bars. It does not say the '
              'accounts achieve outcomes, that 40, 80 or 30 days are the right bars, or that any customer '
              'stayed. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.customer_success as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ca([]) == {'problems': [], 'accounts': [], 'total': 0}
    assert ca([('a', 40, 365)]) == {'problems': [], 'accounts': ['a'], 'total': 1}
    assert ca([('a', 39, 0)])['problems'] == [(0, 'at_risk')]
    assert ca([('a', 0, 0)])['problems'] == [(0, 'at_risk')]
    assert ca([('a', 39, 365)])['problems'] == [(0, 'at_risk')]
    assert ca([('a', 80, 30)])['problems'] == []
    assert ca([('a', 80, 31)])['problems'] == [(0, 'neglected_win')]
    assert ca([('a', 79, 31)])['problems'] == []
    assert ca([('a', 100, 365)])['problems'] == [(0, 'neglected_win')]
    assert ca([('a', 100, 30)])['problems'] == []
    assert ca([('a', 0, 365), ('b', 90, 60), ('c', 60, 60)])['problems'] == [
        (0, 'at_risk'), (1, 'neglected_win')]
    assert ca([('b', 50, 1), ('a', 50, 1)]) == {'problems': [], 'accounts': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4450 + part)
    seen, clean = set(), 0
    for _ in range(60):
        accounts = []
        for _ in range(rnd.randint(0, 9)):
            accounts.append((rnd.choice(('a1', 'a2', 'a3')),
                             rnd.choice((0, 39, 40, 79, 80, 100, rnd.randint(0, 100))),
                             rnd.choice((0, 30, 31, 365, rnd.randint(0, 365)))))
        r = ca(accounts)
        assert r == oracle(accounts)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'at_risk', 'neglected_win'} and clean >= 2


def test_limits_accepted():
    accounts = [('a%02d' % k, 60, 10) for k in range(40)]
    r = ca(accounts)
    assert r['total'] == 40 and r['problems'] == []
    ca([('a' * 24, 100, 365)])
    ca([('a', 0, 0)])


def err(exc, msg, accounts):
    with pytest.raises(exc) as e:
        ca(accounts)
    assert str(e.value) == msg


AM = 'account must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'accounts must be an exact list', bad)
    err(V, 'account count must be at most 40', [('a', 50, 0)] * 41)
    for bad in (None, ['a', 50, 0], 'ab', TupleSub(('a', 50, 0)), 5):
        err(T, 'each account must be an exact tuple', [bad])
    for bad in ((), ('a', 50), ('a', 50, 0, 0)):
        err(V, 'each account must have 3 items', [bad])
    for bad in NS:
        err(T, 'account must be an exact string', [(bad, 50, 0)])
    for bad in BAD:
        err(V, AM, [(bad, 50, 0)])
    for bad in NI:
        err(T, 'health must be an exact integer', [('a', bad, 0)])
        err(T, 'touch_days must be an exact integer', [('a', 50, bad)])
    for bad in (-1, 101, -100, 10**9):
        err(V, 'health must be 0 to 100', [('a', bad, 0)])
    for bad in (-1, 366, -100, 10**9):
        err(V, 'touch_days must be 0 to 365', [('a', 50, bad)])


def _order(err):
    err(T, 'accounts must be an exact list', 'x')
    err(V, 'account count must be at most 40', [None] * 41)
    err(T, 'each account must be an exact tuple', [None, ('a',)])
    err(V, 'each account must have 3 items', [('a',), None])
    err(T, 'account must be an exact string', [(5, -1, -1)])
    err(V, AM, [('A', -1, -1)])
    err(T, 'health must be an exact integer', [('a', '0', -1)])
    err(V, 'health must be 0 to 100', [('a', -1, -1)])
    err(T, 'touch_days must be an exact integer', [('a', 0, '0')])
    err(V, 'touch_days must be 0 to 365', [('a', 0, -1)])
    err(T, 'account must be an exact string', [('a', 50, 0), (5, 50, 0)])
    err(T, 'health must be an exact integer', [('a', 50, 0), ('a', '0', 0)])
    err(T, 'touch_days must be an exact integer', [('a', 50, 0), ('a', 50, '0')])


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
