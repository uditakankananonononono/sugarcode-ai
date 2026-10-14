import random
import pytest
from sugarcode.extra_doc.pestle_analysis import check_scans as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(scans):
    # written from the stated rule: under 6 environment factors is thin; under 2 sources is unsupported
    probs = []
    for i, (_, a, b) in enumerate(scans):
        if a < 6:
            probs.append((i, 'thin_scan'))
        if b < 2:
            probs.append((i, 'unsupported'))
    return {'problems': sorted(probs), 'scans': sorted({x for x, _, _ in scans}), 'total': len(scans)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied scan numbers against two coverage bars. It does not say the '
              'environment is scanned, that 6 factors or 2 sources are the right bars, or that any factor is '
              'real. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.pestle_analysis as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'scans': [], 'total': 0}
    assert ck([('a', 6, 2)]) == {'problems': [], 'scans': ['a'], 'total': 1}
    assert ck([('a', 5, 2)])['problems'] == [(0, 'thin_scan')]
    assert ck([('a', 0, 2)])['problems'] == [(0, 'thin_scan')]
    assert ck([('a', 12, 2)])['problems'] == []
    assert ck([('a', 6, 1)])['problems'] == [(0, 'unsupported')]
    assert ck([('a', 6, 0)])['problems'] == [(0, 'unsupported')]
    assert ck([('a', 5, 1)])['problems'] == [(0, 'thin_scan'), (0, 'unsupported')]
    assert ck([('a', 5, 1), ('b', 6, 2), ('c', 12, 20)])['problems'] == [(0, 'thin_scan'), (0, 'unsupported')]
    assert ck([('b', 6, 2), ('a', 6, 2)]) == {'problems': [], 'scans': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4880 + part)
    seen, clean = set(), 0
    for _ in range(60):
        scans = []
        for _ in range(rnd.randint(0, 9)):
            scans.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 5, 6, 12, rnd.randint(0, 12))),
                          rnd.choice((0, 1, 2, 20, rnd.randint(0, 20)))))
        r = ck(scans)
        assert r == oracle(scans)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'thin_scan', 'unsupported'} and clean >= 2


def test_limits_accepted():
    scans = [('x%02d' % k, 6, 2) for k in range(40)]
    r = ck(scans)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 12, 20)])
    ck([('a', 0, 0)])


def err(exc, msg, scans):
    with pytest.raises(exc) as e:
        ck(scans)
    assert str(e.value) == msg


NM = 'scan must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'scans must be an exact list', bad)
    err(V, 'scan count must be at most 40', [('x', 6, 2)] * 41)
    for bad in (None, ['x', 6, 2], 'ab', TupleSub(('x', 6, 2)), 5):
        err(T, 'each scan must be an exact tuple', [bad])
    for bad in ((), ('x', 6), ('x', 6, 2, 0)):
        err(V, 'each scan must have 3 items', [bad])
    for bad in NS:
        err(T, 'scan must be an exact string', [(bad, 6, 2)])
    for bad in BAD:
        err(V, NM, [(bad, 6, 2)])
    for bad in NI:
        err(T, 'factors must be an exact integer', [('x', bad, 2)])
        err(T, 'sources must be an exact integer', [('x', 6, bad)])
    for bad in (-1, 13, -100, 10**9):
        err(V, 'factors must be 0 to 12', [('x', bad, 2)])
    for bad in (-1, 21, -100, 10**9):
        err(V, 'sources must be 0 to 20', [('x', 6, bad)])


def _order(err):
    err(T, 'scans must be an exact list', 'x')
    err(V, 'scan count must be at most 40', [None] * 41)
    err(T, 'each scan must be an exact tuple', [None, ('x',)])
    err(V, 'each scan must have 3 items', [('x',), None])
    err(T, 'scan must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'factors must be an exact integer', [('x', '0', -1)])
    err(V, 'factors must be 0 to 12', [('x', -1, -1)])
    err(T, 'sources must be an exact integer', [('x', 0, '0')])
    err(V, 'sources must be 0 to 20', [('x', 0, -1)])
    err(T, 'scan must be an exact string', [('x', 6, 2), (5, 6, 2)])
    err(T, 'factors must be an exact integer', [('x', 6, 2), ('x', '0', 2)])
    err(T, 'sources must be an exact integer', [('x', 6, 2), ('x', 6, '0')])


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
