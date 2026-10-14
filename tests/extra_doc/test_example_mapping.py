import random
import pytest
from sugarcode.extra_doc.example_mapping import check_example_map as em

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(rules, qs):
    empty = sorted(n for n, ex in rules if len(ex) == 0)
    allex = [e for _, ex in rules for e in ex]
    shared = sorted({e for e in allex if allex.count(e) > 1})
    openq = sorted(n for n, d in qs if d is False)
    ready = len(rules) > 0 and len(empty) == 0 and len(openq) == 0
    return {'no_examples': empty, 'shared': shared, 'open_questions': openq, 'ready': ready}


def test_hand_cases():
    assert em([('r1', ('a', 'b')), ('r2', ('c',))], [('q1', True)]) == {
        'no_examples': [], 'shared': [], 'open_questions': [], 'ready': True}
    assert em([], []) == {'no_examples': [], 'shared': [], 'open_questions': [], 'ready': False}      # no rules: not ready
    assert em([('r', ())], [])['no_examples'] == ['r'] and em([('r', ())], [])['ready'] is False
    assert em([('r', ('a',))], [('q', False), ('p', True), ('o', False)]) == {
        'no_examples': [], 'shared': [], 'open_questions': ['o', 'q'], 'ready': False}
    assert em([('r', ('a',)), ('s', ('a', 'b')), ('t', ('b',))], [])['shared'] == ['a', 'b']
    assert em([('b', ()), ('a', ())], [])['no_examples'] == ['a', 'b']
    assert em([('r', ('a',))], [])['ready'] is True


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(6850 + part)
    rd = sh = op = ne = 0
    for _ in range(60):
        pool = ['a', 'b', 'c', 'd']
        rules = [('r%d' % i, tuple(rnd.sample(pool, rnd.randint(0, 3)))) for i in range(rnd.randint(0, 4))]
        qs = [('q%d' % i, rnd.random() < 0.7) for i in range(rnd.randint(0, 3))]
        r = em(rules, qs)
        assert r == oracle(rules, qs)
        rd += r['ready']
        sh += bool(r['shared'])
        op += bool(r['open_questions'])
        ne += bool(r['no_examples'])
    assert rd > 1 and sh > 5 and op > 5 and ne > 5


def test_limits_accepted():
    rules = [('r%02d' % i, tuple('e%d' % j for j in range(8))) for i in range(16)]
    qs = [('q%02d' % i, True) for i in range(16)]
    r = em(rules, qs)
    assert r['ready'] is True and len(r['shared']) == 8
    em([('a' * 24, ('b' * 24,))], [('c' * 24, False)])


def err(exc, msg, r, q):
    with pytest.raises(exc) as e:
        em(r, q)
    assert str(e.value) == msg


NM = 'name must be 1 to 24 lowercase identifier characters'
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
NS = (None, 5, b'a', StrSub('a'))
R = [('r', ('a',))]


def _pins(err):
    for bad in (None, (), 'ab', ListSub(R), {}):
        err(T, 'rules must be an exact list', bad, [])
    err(V, 'rule count must be at most 16', [('r%02d' % i, ()) for i in range(17)], [])
    for bad in (None, ['r', ()], 'ab', TupleSub(('r', ())), 5):
        err(T, 'each rule must be an exact tuple', [bad], [])
    for bad in ((), ('r',), ('r', (), 1)):
        err(V, 'each rule must have 2 items', [bad], [])
    for bad in NS:
        err(T, 'name must be an exact string', [(bad, ())], [])
        err(T, 'name must be an exact string', [('r', (bad,))], [])
        err(T, 'name must be an exact string', R, [(bad, True)])
    for bad in BAD:
        err(V, NM, [(bad, ())], [])
        err(V, NM, [('r', (bad,))], [])
        err(V, NM, R, [(bad, True)])
    for bad in (None, ['a'], 'a', TupleSub(('a',)), {}):
        err(T, 'examples must be an exact tuple', [('r', bad)], [])
    err(V, 'example count must be at most 8', [('r', tuple('e%d' % i for i in range(9)))], [])
    err(V, 'repeated example in a rule', [('r', ('a', 'b', 'a'))], [])
    err(V, 'duplicate rule name', [('r', ()), ('r', ('a',))], [])
    for bad in (None, (), 'ab', ListSub([('q', True)]), {}):
        err(T, 'questions must be an exact list', R, bad)
    err(V, 'question count must be at most 16', R, [('q%02d' % i, True) for i in range(17)])
    for bad in (None, ['q', True], 'qt', TupleSub(('q', True)), 5):
        err(T, 'each question must be an exact tuple', R, [bad])
    for bad in ((), ('q',), ('q', True, 1)):
        err(V, 'each question must have 2 items', R, [bad])
    for bad in (None, 1, 0, 'True', [], 2):
        err(T, 'resolved must be an exact bool', R, [('q', bad)])
    err(V, 'duplicate question name', R, [('q', True), ('p', False), ('q', False)])


def _order(err):
    err(T, 'rules must be an exact list', 'x', 'y')
    err(V, 'rule count must be at most 16', [None] * 17, 'y')
    err(T, 'each rule must be an exact tuple', [None, ('a',)], 'y')
    err(V, 'each rule must have 2 items', [('a',), None], 'y')
    err(V, NM, [('A', 5)], 'y')
    err(T, 'name must be an exact string', [(5, 5)], 'y')
    err(T, 'examples must be an exact tuple', [('r', 5)], 'y')
    err(V, 'example count must be at most 8', [('r', (5,) * 9)], 'y')
    err(T, 'name must be an exact string', [('r', (5, 'A'))], 'y')
    err(V, NM, [('r', ('A', 5))], 'y')
    err(V, 'repeated example in a rule', [('r', ('a', 'a')), ('r', 5)], 'y')
    err(T, 'examples must be an exact tuple', [('r', ()), ('s', 5), ('r', ())], 'y')
    err(V, 'duplicate rule name', [('r', ()), ('r', ())], 'y')
    err(T, 'questions must be an exact list', R, 'y')
    err(V, 'question count must be at most 16', R, [None] * 17)
    err(T, 'each question must be an exact tuple', R, [None, ('a',)])
    err(V, 'each question must have 2 items', R, [('a',), None])
    err(V, NM, R, [('A', 5)])
    err(T, 'name must be an exact string', R, [(5, 5)])
    err(T, 'resolved must be an exact bool', R, [('q', 5), (5, True)])
    err(T, 'name must be an exact string', R, [(5, True), ('q', 5)])
    err(V, 'duplicate question name', R, [('q', True), ('q', True)])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,r,q', _collect(_pins))
def test_pin(exc, msg, r, q):
    err(exc, msg, r, q)


@pytest.mark.parametrize('exc,msg,r,q', _collect(_order))
def test_order(exc, msg, r, q):
    err(exc, msg, r, q)
