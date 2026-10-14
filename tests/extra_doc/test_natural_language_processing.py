import random
import pytest
from sugarcode.extra_doc.natural_language_processing import check_pipelines as ck

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
    # written from the stated rule: under 100 documents is tiny corpus; under 2 languages is monolingual
    probs = []
    for i, (_, a, b) in enumerate(items):
        if a < 100:
            probs.append((i, 'tiny_corpus'))
        if b < 2:
            probs.append((i, 'monolingual'))
    return {'problems': sorted(probs), 'pipelines': sorted({x for x, _, _ in items}), 'total': len(items)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied pipeline numbers against two text bars. It does not say text is understood, that 100 documents or 2 languages are the right bars, or that any output is right. No clinical or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.natural_language_processing as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert ck([]) == {'problems': [], 'pipelines': [], 'total': 0}
    assert ck([('a', 1000, 5)]) == {'problems': [], 'pipelines': ['a'], 'total': 1}
    assert ck([('a', 99, 5)])['problems'] == [(0, 'tiny_corpus')]
    assert ck([('a', 0, 5)])['problems'] == [(0, 'tiny_corpus')]
    assert ck([('a', 1000, 1)])['problems'] == [(0, 'monolingual')]
    assert ck([('a', 1000, 0)])['problems'] == [(0, 'monolingual')]
    assert ck([('a', 99, 1)])['problems'] == [((0, 'monolingual')), ((0, 'tiny_corpus'))]
    assert ck([('a', 99, 1), ('b', 1000, 5), ('c', 0, 5)])['problems'] == [
        (0, 'monolingual'), (0, 'tiny_corpus'), (2, 'tiny_corpus')]
    assert ck([('b', 1000, 5), ('a', 1000, 5)]) == {'problems': [], 'pipelines': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(5540 + part)
    seen, clean = set(), 0
    for _ in range(60):
        items = []
        for _ in range(rnd.randint(0, 9)):
            items.append((rnd.choice(('x1', 'x2', 'x3')),
                          rnd.choice((0, 99, 100, 100000, rnd.randint(0, 100000))),
                          rnd.choice((0, 1, 2, 50, rnd.randint(0, 50)))))
        r = ck(items)
        assert r == oracle(items)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'tiny_corpus', 'monolingual'} and clean >= 2


def test_limits_accepted():
    items = [('x%02d' % k, 1000, 5) for k in range(40)]
    r = ck(items)
    assert r['total'] == 40 and r['problems'] == []
    ck([('a' * 24, 100000, 50)])
    ck([('a', 0, 0)])


def err(exc, msg, items):
    with pytest.raises(exc) as e:
        ck(items)
    assert str(e.value) == msg


NM = 'pipeline must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'pipelines must be an exact list', bad)
    err(V, 'pipeline count must be at most 40', [('x', 1000, 5)] * 41)
    for bad in (None, ['x', 1000, 5], 'ab', TupleSub(('x', 1000, 5)), 5):
        err(T, 'each pipeline must be an exact tuple', [bad])
    for bad in ((), ('x', 1000), ('x', 1000, 5, 0)):
        err(V, 'each pipeline must have 3 items', [bad])
    for bad in NS:
        err(T, 'pipeline must be an exact string', [(bad, 1000, 5)])
    for bad in BAD:
        err(V, NM, [(bad, 1000, 5)])
    for bad in NI:
        err(T, 'docs' + ' must be an exact integer', [('x', bad, 5)])
        err(T, 'languages' + ' must be an exact integer', [('x', 1000, bad)])
    for bad in (-1, 100001, -100, 10**9):
        err(V, 'docs' + ' must be 0 to 100000', [('x', bad, 5)])
    for bad in (-1, 51, -100, 10**9):
        err(V, 'languages' + ' must be 0 to 50', [('x', 1000, bad)])


def _order(err):
    err(T, 'pipelines must be an exact list', 'x')
    err(V, 'pipeline count must be at most 40', [None] * 41)
    err(T, 'each pipeline must be an exact tuple', [None, ('x',)])
    err(V, 'each pipeline must have 3 items', [('x',), None])
    err(T, 'pipeline must be an exact string', [(5, -1, -1)])
    err(V, NM, [('A', -1, -1)])
    err(T, 'docs' + ' must be an exact integer', [('x', '0', -1)])
    err(V, 'docs' + ' must be 0 to 100000', [('x', -1, -1)])
    err(T, 'languages' + ' must be an exact integer', [('x', 0, '0')])
    err(V, 'languages' + ' must be 0 to 50', [('x', 0, -1)])
    err(T, 'pipeline must be an exact string', [('x', 1000, 5), (5, 1000, 5)])
    err(T, 'docs' + ' must be an exact integer', [('x', 1000, 5), ('x', '0', 5)])
    err(T, 'languages' + ' must be an exact integer', [('x', 1000, 5), ('x', 1000, '0')])


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
