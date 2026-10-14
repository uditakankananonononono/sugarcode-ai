import random
import pytest
from sugarcode.extra_doc.behavior_driven_development import check_scenario as cs

T, V = TypeError, ValueError
KW = ['Given', 'When', 'Then', 'And', 'But']


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(steps):
    order = ['Given', 'When', 'Then']
    eff, probs, last = [], [], None
    for i, (k, _) in enumerate(steps):
        if k in order:
            cur = k
        else:
            cur = last
            if i == 0:
                probs.append((0, 'and_first'))
        if cur is not None and last is not None and order.index(cur) < order.index(last):
            probs.append((i, 'out_of_order'))
        eff.append(cur)
        last = cur
    if order[1] not in eff:
        probs.append((-1, 'no_when'))
    if order[2] not in eff:
        probs.append((-1, 'no_then'))
    return {'effective': eff, 'problems': sorted(probs)}


def test_hand_cases():
    assert cs([('Given', 'a'), ('And', 'b'), ('When', 'c'), ('Then', 'd'), ('But', 'e')]) == {
        'effective': ['Given', 'Given', 'When', 'Then', 'Then'], 'problems': []}
    assert cs([]) == {'effective': [], 'problems': [(-1, 'no_then'), (-1, 'no_when')]}
    assert cs([('When', 'a'), ('Then', 'b')])['problems'] == []                      # Given is optional
    assert cs([('Then', 'a'), ('When', 'b')]) == {'effective': ['Then', 'When'], 'problems': [(1, 'out_of_order')]}
    assert cs([('When', 'a'), ('Given', 'b'), ('Then', 'c')])['problems'] == [(1, 'out_of_order')]
    assert cs([('And', 'a'), ('Then', 'b'), ('When', 'c')]) == {
        'effective': [None, 'Then', 'When'], 'problems': [(0, 'and_first'), (2, 'out_of_order')]}
    assert cs([('But', 'a'), ('And', 'b')]) == {'effective': [None, None], 'problems': [(-1, 'no_then'), (-1, 'no_when'),
                                                                                         (0, 'and_first')]}
    assert cs([('When', 'a'), ('Then', 'b'), ('And', 'c'), ('When', 'd')])['problems'] == [(3, 'out_of_order')]
    assert cs([('Given', 'a'), ('Given', 'b'), ('When', 'c'), ('When', 'd'), ('Then', 'e'), ('Then', 'f')])['problems'] == []


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(6860 + part)
    seen, clean = set(), 0
    for _ in range(60):
        if rnd.random() < 0.5:
            base = ['Given'] * rnd.randint(0, 2) + ['When'] * rnd.randint(1, 2) + ['Then'] * rnd.randint(1, 2)
            steps = [(k if i == 0 or rnd.random() < 0.6 else rnd.choice(['And', 'But']), 'x') for i, k in enumerate(base)]
        else:
            steps = [(rnd.choice(KW), 'x') for _ in range(rnd.randint(0, 6))]
        r = cs(steps)
        assert r == oracle(steps)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) == 4 and clean > 5


def test_limits_accepted():
    steps = [('Given', 'a')] * 20 + [('When', 'b')] * 10 + [('Then', 'c')] * 10
    assert len(steps) == 40 and cs(steps)['problems'] == []
    cs([('When', 'a' * 80), ('Then', '~'), ('And', 'a b ~')])


def err(exc, msg, steps):
    with pytest.raises(exc) as e:
        cs(steps)
    assert str(e.value) == msg


KM = "keyword must be 'Given', 'When', 'Then', 'And' or 'But'"
TM = 'text must be printable ASCII with no leading or trailing space'
LM = 'text must be 1 to 80 characters'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'steps must be an exact list', bad)
    err(V, 'step count must be at most 40', [('When', 'a')] * 41)
    for bad in (None, ['When', 'a'], 'Wa', TupleSub(('When', 'a')), 5):
        err(T, 'each step must be an exact tuple', [bad])
    for bad in ((), ('When',), ('When', 'a', 1)):
        err(V, 'each step must have 2 items', [bad])
    for bad in (None, 5, b'When', StrSub('When')):
        err(T, 'keyword must be an exact string', [(bad, 'a')])
        err(T, 'text must be an exact string', [('When', bad)])
    for bad in ('', 'when', 'WHEN', 'When ', 'Given ', 'And then', 'é'):
        err(V, KM, [(bad, 'a')])
    err(V, LM, [('When', '')])
    err(V, LM, [('When', 'a' * 81)])
    for bad in (' a', 'a ', ' ', 'a\n', '\ta', 'é', 'a\x7f', 'a\x1f', 'ａ', 'a\u00a0'):
        err(V, TM, [('When', bad)])


def _order(err):
    err(T, 'steps must be an exact list', 'x')
    err(V, 'step count must be at most 40', [None] * 41)
    err(T, 'each step must be an exact tuple', [None, ('a',)])
    err(V, 'each step must have 2 items', [('a',), None])
    err(T, 'keyword must be an exact string', [(5, 5)])
    err(V, KM, [('zz', 5)])
    err(T, 'text must be an exact string', [('When', 5), ('zz', 'a')])
    err(V, LM, [('When', ''), ('zz', 'a')])
    err(V, TM, [('When', ' '), ('zz', 'a')])
    err(V, TM, [('When', 'é')])
    err(V, LM, [('When', 'é' * 81)])
    err(V, KM, [('zz', 'a'), ('When', 5)])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,s', _collect(_pins))
def test_pin(exc, msg, s):
    err(exc, msg, s)


@pytest.mark.parametrize('exc,msg,s', _collect(_order))
def test_order(exc, msg, s):
    err(exc, msg, s)
