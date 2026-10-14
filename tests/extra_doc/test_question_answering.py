import random
import pytest
from sugarcode.extra_doc.question_answering import check_systems as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(items):
    # written from the stated rule: under 80 percent coverage is low; over 500 ms is slow
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 80:
            probs.append((i, 'low_coverage'))
        if b > 500:
            probs.append((i, 'slow_answer'))
    return {'problems': sorted(probs), 'systems': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied evaluation numbers against two answer bars. It does not say queries are answered, that 80 percent or 500 ms are the right bars, or that any answer is right. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.question_answering as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'systems': [], 'total': 0}
    assert ck([('a', 90, 100)]) == {'problems': [], 'systems': ['a'], 'total': 1}
    assert ck([('a', 79, 100)])['problems'] == [(0, 'low_coverage')]
    assert ck([('a', 0, 100)])['problems'] == [(0, 'low_coverage')]
    assert ck([('a', 90, 501)])['problems'] == [(0, 'slow_answer')]
    assert ck([('a', 90, 10000)])['problems'] == [(0, 'slow_answer')]
    assert ck([('a', 79, 501)])['problems'] == [((0, 'low_coverage')), ((0, 'slow_answer'))]
    assert ck([('a', 79, 501), ('b', 90, 100), ('c', 0, 100)])['problems'] == [
        (0, 'low_coverage'), (0, 'slow_answer'), (2, 'low_coverage')]
    assert ck([('b', 90, 100), ('a', 90, 100)]) == {'problems': [], 'systems': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(5600 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 79, 80, 100, rnd.randint(0, 100))),
                          rnd.choice((0, 500, 501, 10000, rnd.randint(0, 10000)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'low_coverage', 'slow_answer'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 90, 100) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 100, 10000)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'system must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'systems must be an exact list', bad)
    err(V, 'system count must be at most 40', [('x', 90, 100)] * 41)
    for bad in (None, ['x', 90, 100], 'ab', TupleSub(('x', 90, 100)), 5):
        err(T, 'each system must be an exact tuple', [bad])
    for bad in ((), ('x', 90), ('x', 90, 100, 0)):
        err(V, 'each system must have 3 items', [bad])
    for bad in NS:
        err(T, 'system must be an exact string', [(bad, 90, 100)])
    for bad in BAD:
        err(V, NM, [(bad, 90, 100)])
    for bad in NI:
        err(T, 'coverage' + ' must be an exact integer', [('x', bad, 100)])
        err(T, 'latency_ms' + ' must be an exact integer', [('x', 90, bad)])
    for bad in (-1, 101, -100, 10**9):
        err(V, 'coverage' + ' must be 0 to 100', [('x', bad, 100)])
    for bad in (-1, 10001, -100, 10**9):
        err(V, 'latency_ms' + ' must be 0 to 10000', [('x', 90, bad)])


def _order(err):
    err(T, 'systems must be an exact list', 'x')
    err(V, 'system count must be at most 40', [None] * 41)
    err(T, 'each system must be an exact tuple', [None, ('x',)])
    err(V, 'each system must have 3 items', [('x',), None])
    err(T, 'system must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'coverage' + ' must be an exact integer', [('x', '0', -1)])
    err(V, 'coverage' + ' must be 0 to 100', [('x', -1, -1)])
    err(T, 'latency_ms' + ' must be an exact integer', [('x', 0, '0')])
    err(V, 'latency_ms' + ' must be 0 to 10000', [('x', 0, -1)])
    err(T, 'system must be an exact string', [('x', 90, 100), (5, 90, 100)])
    err(T, 'coverage' + ' must be an exact integer', [('x', 90, 100), ('x', '0', 100)])
    err(T, 'latency_ms' + ' must be an exact integer', [('x', 90, 100), ('x', 90, '0')])


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
