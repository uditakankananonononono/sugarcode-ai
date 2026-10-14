import random
import pytest
from sugarcode.extra_doc.ports_and_adapters import check_wiring as cw

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(ports, adapters, core):
    out = []
    for p in ports:
        mine = [s for _, q, s in adapters if q == p]
        if not mine:
            out.append((p, 'no_adapter'))
        elif 'driving' in mine and 'driven' in mine:
            out.append((p, 'mixed_sides'))
        if core.count(p) == 0:
            out.append((p, 'not_in_core'))
    return {'problems': sorted(out)}


def test_hand_cases():
    assert cw(['a'], [('x', 'a', 'driving')], ['a']) == {'problems': []}
    assert cw(['a'], [], ['a']) == {'problems': [('a', 'no_adapter')]}
    assert cw(['a'], [('x', 'a', 'driving'), ('y', 'a', 'driving')], ['a']) == {'problems': []}
    assert cw(['a'], [('x', 'a', 'driving'), ('y', 'a', 'driven')], ['a']) == {'problems': [('a', 'mixed_sides')]}
    assert cw(['a'], [('x', 'a', 'driven')], []) == {'problems': [('a', 'not_in_core')]}
    assert cw(['b', 'a'], [], []) == {'problems': [('a', 'no_adapter'), ('a', 'not_in_core'), ('b', 'no_adapter'),
                                                  ('b', 'not_in_core')]}
    assert cw(['a'], [('x', 'a', 'driven'), ('y', 'a', 'driving'), ('z', 'a', 'driven')], [])['problems'] == [
        ('a', 'mixed_sides'), ('a', 'not_in_core')]


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(6820 + part)
    k = {'no_adapter': 0, 'mixed_sides': 0, 'not_in_core': 0, 'clean': 0}
    for _ in range(60):
        ports = rnd.sample(['p0', 'p1', 'p2', 'p3'], rnd.randint(1, 4))
        ads = [('a%d' % i, rnd.choice(ports), rnd.choice(['driving', 'driven'])) for i in range(rnd.randint(0, 6))]
        core = rnd.sample(ports, rnd.randint(0, len(ports)))
        r = cw(ports, ads, core)
        assert r == oracle(ports, ads, core)
        for _, c in r['problems']:
            k[c] += 1
        k['clean'] += not r['problems']
    assert all(v > 1 for v in k.values())


def test_limits_accepted():
    ports = ['p%02d' % i for i in range(16)]
    ads = [('a%02d' % i, ports[i % 16], 'driving') for i in range(32)]
    assert cw(ports, ads, ports) == {'problems': []}
    cw(['a' * 24], [('b' * 24, 'a' * 24, 'driven')], ['a' * 24])


def err(exc, msg, p, a, c):
    with pytest.raises(exc) as e:
        cw(p, a, c)
    assert str(e.value) == msg


P = ['a', 'b']
A = [('x', 'a', 'driving')]
NM = 'name must be 1 to 24 lowercase identifier characters'
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
NS = (None, 5, b'a', StrSub('a'))


def _pins(err):
    for bad in (None, (), 'ab', ListSub(P), {}):
        err(T, 'ports must be an exact list', bad, [], [])
    err(V, 'port count must be between 1 and 16', [], [], [])
    err(V, 'port count must be between 1 and 16', ['p%02d' % i for i in range(17)], [], [])
    for bad in NS:
        err(T, 'name must be an exact string', [bad], [], [])
        err(T, 'name must be an exact string', P, [(bad, 'a', 'driving')], [])
        err(T, 'name must be an exact string', P, [('x', bad, 'driving')], [])
        err(T, 'name must be an exact string', P, [], [bad])
    for bad in BAD:
        err(V, NM, [bad], [], [])
        err(V, NM, P, [(bad, 'a', 'driving')], [])
        err(V, NM, P, [('x', bad, 'driving')], [])
        err(V, NM, P, [], [bad])
    err(V, 'duplicate port', ['a', 'b', 'a'], [], [])
    for bad in (None, (), 'ab', ListSub(A), {}):
        err(T, 'adapters must be an exact list', P, bad, [])
    err(V, 'adapter count must be at most 32', P, [('x%02d' % i, 'a', 'driving') for i in range(33)], [])
    for bad in (None, ['x', 'a', 'driving'], 'xad', TupleSub(('x', 'a', 'driving')), 5):
        err(T, 'each adapter must be an exact tuple', P, [bad], [])
    for bad in ((), ('x', 'a'), ('x', 'a', 'driving', 1)):
        err(V, 'each adapter must have 3 items', P, [bad], [])
    for bad in (None, 5, b'driving', StrSub('driving')):
        err(T, 'side must be an exact string', P, [('x', 'a', bad)], [])
    for bad in ('', 'Driving', 'driving ', 'left', 'in'):
        err(V, "side must be 'driving' or 'driven'", P, [('x', 'a', bad)], [])
    err(V, 'duplicate adapter', P, [('x', 'a', 'driving'), ('x', 'b', 'driven')], [])
    err(V, 'unknown port: z', P, [('x', 'z', 'driving')], [])
    for bad in (None, (), 'ab', ListSub(['a']), {}):
        err(T, 'core_ports must be an exact list', P, A, bad)
    err(V, 'core_ports count must be at most 16', P, A, ['p%02d' % i for i in range(17)])
    err(V, 'repeated core port', P, A, ['a', 'b', 'a'])
    err(V, 'unknown port: z', P, A, ['z'])


def _order(err):
    err(T, 'ports must be an exact list', 'x', 'y', 'z')
    err(V, 'port count must be between 1 and 16', [], 'y', 'z')
    err(T, 'name must be an exact string', [5, 'A'], 'y', 'z')
    err(V, NM, ['A', 5], 'y', 'z')
    err(V, NM, ['A', 'A'], 'y', 'z')
    err(V, 'duplicate port', ['a', 'a'], 'y', 'z')
    err(T, 'adapters must be an exact list', P, 'y', 'z')
    err(V, 'adapter count must be at most 32', P, [None] * 33, 'z')
    err(T, 'each adapter must be an exact tuple', P, [None, ('x',)], 'z')
    err(V, 'each adapter must have 3 items', P, [('x',), None], 'z')
    err(V, NM, P, [('A', 5, 5)], 'z')
    err(T, 'name must be an exact string', P, [(5, 'A', 5)], 'z')
    err(V, NM, P, [('x', 'A', 5)], 'z')
    err(T, 'name must be an exact string', P, [('x', 5, 5)], 'z')
    err(T, 'side must be an exact string', P, [('x', 'a', 5)], 'z')
    err(V, "side must be 'driving' or 'driven'", P, [('x', 'a', 'zz'), (5, 'a', 'driving')], 'z')
    err(V, 'duplicate adapter', P, [('x', 'q', 'driving'), ('x', 'q', 'driving')], 'z')
    err(V, 'unknown port: q', P, [('x', 'q', 'driving')], 'z')
    err(T, 'core_ports must be an exact list', P, A, 'z')
    err(V, 'core_ports count must be at most 16', P, A, [None] * 17)
    err(T, 'name must be an exact string', P, A, [5, 'A'])
    err(V, NM, P, A, ['A', 5])
    err(V, 'repeated core port', P, A, ['q', 'q'])
    err(V, 'unknown port: q', P, A, ['q', 'z'])


def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,p,a,c', _collect(_pins))
def test_pin(exc, msg, p, a, c):
    err(exc, msg, p, a, c)


@pytest.mark.parametrize('exc,msg,p,a,c', _collect(_order))
def test_order(exc, msg, p, a, c):
    err(exc, msg, p, a, c)
