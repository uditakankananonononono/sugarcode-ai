import random
import pytest
from sugarcode.extra_doc.swot_analysis import check_subjects as ck

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(subjects):
    # written from the stated rule: under 1 factor on either side is one_sided; under 4 in total is shallow
    probs = []
    for i, (_, a, b) in enumerate(subjects):
        if a < 1 or b < 1:
            probs.append((i, 'one_sided'))
        if a + b < 4:
            probs.append((i, 'shallow'))
    return {'problems': sorted(probs), 'subjects': sorted({x for x, _, _ in subjects}), 'total': len(subjects)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied factor counts against two position bars. It does not say the '
              'position is assessed, that 1 factor a side or 4 in total are the right bars, or that any factor '
              'is real. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.swot_analysis as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'subjects': [], 'total': 0}
    assert ck([('a', 2, 2)]) == {'problems': [], 'subjects': ['a'], 'total': 1}
    assert ck([('a', 0, 5)])['problems'] == [(0, 'one_sided')]
    assert ck([('a', 5, 0)])['problems'] == [(0, 'one_sided')]
    assert ck([('a', 2, 1)])['problems'] == [(0, 'shallow')]
    assert ck([('a', 1, 2)])['problems'] == [(0, 'shallow')]
    assert ck([('a', 1, 3)])['problems'] == []
    assert ck([('a', 0, 0)])['problems'] == [(0, 'one_sided'), (0, 'shallow')]
    assert ck([('a', 0, 0), ('b', 4, 4), ('c', 20, 20)])['problems'] == [(0, 'one_sided'), (0, 'shallow')]
    assert ck([('b', 4, 4), ('a', 4, 4)]) == {'problems': [], 'subjects': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4870 + part)
    seen, clean = set(), 0
    for _ in range(60):
        subjects = []
        for _ in range(rnd.randint(0, 9)):
            subjects.append((rnd.choice(('x1', 'x2', 'x3')),
                             rnd.choice((0, 1, 2, 20, rnd.randint(0, 20))),
                             rnd.choice((0, 1, 2, 20, rnd.randint(0, 20)))))
        r = ck(subjects)
        assert r == oracle(subjects)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'one_sided', 'shallow'} and clean >= 2


def test_limits_accepted():
    subjects = [('x%02d' % k, 2, 2) for k in range(40)]
    r = ck(subjects)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 20, 20)])
    ck([('a', 0, 0)])


def err(exc, msg, subjects):
    with pytest.raises(exc) as e:
        ck(subjects)
    assert str(e.value) == msg


NM = 'subject must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'subjects must be an exact list', bad)
    err(V, 'subject count must be at most 40', [('x', 5, 5)] * 41)
    for bad in (None, ['x', 5, 5], 'ab', TupleSub(('x', 5, 5)), 5):
        err(T, 'each subject must be an exact tuple', [bad])
    for bad in ((), ('x', 5), ('x', 5, 5, 0)):
        err(V, 'each subject must have 3 items', [bad])
    for bad in NS:
        err(T, 'subject must be an exact string', [(bad, 5, 5)])
    for bad in BAD:
        err(V, NM, [(bad, 5, 5)])
    for bad in NI:
        err(T, 'positives must be an exact integer', [('x', bad, 5)])
        err(T, 'negatives must be an exact integer', [('x', 5, bad)])
    for bad in (-1, 21, -100, 10**9):
        err(V, 'positives must be 0 to 20', [('x', bad, 5)])
    for bad in (-1, 21, -100, 10**9):
        err(V, 'negatives must be 0 to 20', [('x', 5, bad)])


def _order(err):
    err(T, 'subjects must be an exact list', 'x')
    err(V, 'subject count must be at most 40', [None] * 41)
    err(T, 'each subject must be an exact tuple', [None, ('x',)])
    err(V, 'each subject must have 3 items', [('x',), None])
    err(T, 'subject must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'positives must be an exact integer', [('x', '0', -1)])
    err(V, 'positives must be 0 to 20', [('x', -1, -1)])
    err(T, 'negatives must be an exact integer', [('x', 0, '0')])
    err(V, 'negatives must be 0 to 20', [('x', 0, -1)])
    err(T, 'subject must be an exact string', [('x', 5, 5), (5, 5, 5)])
    err(T, 'positives must be an exact integer', [('x', 5, 5), ('x', '0', 5)])
    err(T, 'negatives must be an exact integer', [('x', 5, 5), ('x', 5, '0')])


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
