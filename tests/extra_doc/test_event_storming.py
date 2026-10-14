import itertools
import random
import pytest
from sugarcode.extra_doc.event_storming import check_timeline as ct

T, V = TypeError, ValueError
KINDS = ['actor', 'command', 'policy', 'event']


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


# what may sit right after each kind (None = end of timeline), and what may sit right before it
NEXT = {'actor': {'command'}, 'command': {'event'}, 'policy': {'command'}}
PREV = {'command': {'actor', 'policy'}, 'policy': {'event'}}


def oracle(st):
    ks = [k for k, _ in st]
    probs = []
    for i, k in enumerate(ks):
        nxt = ks[i + 1] if i + 1 < len(ks) else None
        prv = ks[i - 1] if i else None
        if k in NEXT and nxt not in NEXT[k]:
            probs.append((i, k + '_without_' + sorted(NEXT[k])[0]))
        if k in PREV and prv not in PREV[k]:
            probs.append((i, k + '_without_' + ('trigger' if k == 'command' else 'event')))
    return {'problems': sorted(probs), 'counts': {k: sum(1 for x in ks if x == k) for k in KINDS},
            'events': [n for k, n in st if k == 'event']}


def test_hand_cases():
    ok = [('actor', 'clerk'), ('command', 'place_order'), ('event', 'order_placed'), ('policy', 'auto_ship'),
          ('command', 'ship'), ('event', 'shipped')]
    assert ct(ok) == {'problems': [], 'counts': {'actor': 1, 'command': 2, 'policy': 1, 'event': 2},
                      'events': ['order_placed', 'shipped']}
    assert ct([]) == {'problems': [], 'counts': {'actor': 0, 'command': 0, 'policy': 0, 'event': 0}, 'events': []}
    assert ct([('event', 'a')])['problems'] == []
    assert ct([('actor', 'a')])['problems'] == [(0, 'actor_without_command')]
    assert ct([('command', 'a')])['problems'] == [(0, 'command_without_event'), (0, 'command_without_trigger')]
    assert ct([('policy', 'a')])['problems'] == [(0, 'policy_without_command'), (0, 'policy_without_event')]
    assert ct([('actor', 'a'), ('command', 'b'), ('event', 'c')])['problems'] == []
    assert ct([('event', 'e'), ('command', 'c'), ('event', 'f')])['problems'] == [(1, 'command_without_trigger')]
    assert ct([('actor', 'a'), ('actor', 'b'), ('command', 'c'), ('event', 'e')])['problems'] == [(0, 'actor_without_command')]
    assert ct([('event', 'e'), ('policy', 'p'), ('command', 'c'), ('event', 'f')])['problems'] == []
    assert ct([('actor', 'a'), ('policy', 'p'), ('command', 'c'), ('event', 'f')])['problems'] == [
        (0, 'actor_without_command'), (1, 'policy_without_event')]
    assert ct([('actor', 'a'), ('command', 'c'), ('command', 'd'), ('event', 'e')])['problems'] == [
        (1, 'command_without_event'), (2, 'command_without_trigger')]


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(6840 + part)
    seen, clean = set(), 0
    for _ in range(60):
        st = [(rnd.choice(KINDS), rnd.choice(['a', 'b', 'c'])) for _ in range(rnd.randint(0, 7))]
        r = ct(st)
        assert r == oracle(st)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) >= 5 and clean > 1


def test_every_short_timeline_matches_oracle():
    for n in range(0, 5):
        for kinds in itertools.product(KINDS, repeat=n):
            st = [(k, 'n') for k in kinds]
            assert ct(st) == oracle(st)


def test_limits_accepted():
    st = [('actor', 'a'), ('command', 'c')] + [('event', 'e')] * 62
    assert len(ct(st)['events']) == 62 and ct(st)['problems'] == []
    ct([('event', 'a' * 24)])


def err(exc, msg, st):
    with pytest.raises(exc) as e:
        ct(st)
    assert str(e.value) == msg


KM = "kind must be 'actor', 'command', 'policy' or 'event'"
NM = 'name must be 1 to 24 lowercase identifier characters'
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'stickies must be an exact list', bad)
    err(V, 'sticky count must be at most 64', [('event', 'a')] * 65)
    for bad in (None, ['event', 'a'], 'ea', TupleSub(('event', 'a')), 5):
        err(T, 'each sticky must be an exact tuple', [bad])
    for bad in ((), ('event',), ('event', 'a', 1)):
        err(V, 'each sticky must have 2 items', [bad])
    for bad in (None, 5, b'event', StrSub('event')):
        err(T, 'kind must be an exact string', [(bad, 'a')])
        err(T, 'name must be an exact string', [('event', bad)])
    for bad in ('', 'Event', 'event ', 'task', 'events', 'é'):
        err(V, KM, [(bad, 'a')])
    for bad in BAD:
        err(V, NM, [('event', bad)])


def _order(err):
    err(T, 'stickies must be an exact list', 'x')
    err(V, 'sticky count must be at most 64', [None] * 65)
    err(T, 'each sticky must be an exact tuple', [None, ('a',)])
    err(V, 'each sticky must have 2 items', [('a',), None])
    err(T, 'kind must be an exact string', [(5, 5)])
    err(V, KM, [('zz', 5)])
    err(T, 'name must be an exact string', [('event', 5), ('zz', 'a')])
    err(V, NM, [('event', 'A'), (5, 'a')])
    err(V, KM, [('zz', 'a'), ('event', 5)])


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
