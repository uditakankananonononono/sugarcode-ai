import random
import pytest
from sugarcode.extra_doc.code_review import check_review as cr

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(author, reviews, comments):
    last = {}
    for who, v in reviews:
        if who == author:
            continue
        last[who] = v
    appr = sorted(w for w in last if last[w] == 'approve')
    blocks = set()
    if len(appr) <= 1:
        blocks.add('needs_two_approvals')
    if any(last[w] == 'request_changes' for w in last):
        blocks.add('changes_requested')
    for _, sev, done in comments:
        if sev in ('blocker', 'major') and done is False:
            blocks.add('open_blocking')
    return {'approvals': appr, 'blocks': sorted(blocks), 'mergeable': not blocks}


def test_hand_cases():
    ok = [('b', 'approve'), ('c', 'approve')]
    assert cr('a', ok, []) == {'approvals': ['b', 'c'], 'blocks': [], 'mergeable': True}
    assert cr('a', ok[:1], []) == {'approvals': ['b'], 'blocks': ['needs_two_approvals'], 'mergeable': False}
    assert cr('a', [], [])['blocks'] == ['needs_two_approvals']
    assert cr('a', ok + [('a', 'approve')], [])['approvals'] == ['b', 'c']             # the author's review is ignored
    assert cr('a', [('a', 'approve'), ('b', 'approve')], [])['blocks'] == ['needs_two_approvals']
    assert cr('a', [('b', 'approve'), ('b', 'approve'), ('c', 'comment')], [])['approvals'] == ['b']   # one reviewer counts once
    r = cr('a', ok + [('c', 'request_changes')], [])
    assert r['approvals'] == ['b'] and r['blocks'] == ['changes_requested', 'needs_two_approvals']
    r = cr('a', [('c', 'request_changes')] + ok, [])                                    # the latest verdict wins
    assert r['mergeable'] is True
    assert cr('a', ok + [('c', 'comment')], [])['approvals'] == ['b']                   # a later comment replaces an approval
    assert cr('a', ok, [('x', 'blocker', False)])['blocks'] == ['open_blocking']
    assert cr('a', ok, [('x', 'major', False)])['blocks'] == ['open_blocking']
    assert cr('a', ok, [('x', 'minor', False), ('y', 'nit', False), ('z', 'blocker', True)])['mergeable'] is True
    assert cr('a', [('b', 'request_changes')], [('x', 'major', False)])['blocks'] == [
        'changes_requested', 'needs_two_approvals', 'open_blocking']
    assert cr('a', [('a', 'request_changes')] + ok, [])['mergeable'] is True            # author's request_changes ignored


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(6900 + part)
    seen, ok = set(), 0
    for _ in range(60):
        reviews = [(rnd.choice(['a', 'b', 'c', 'd']), rnd.choice(['approve', 'approve', 'request_changes', 'comment']))
                   for _ in range(rnd.randint(0, 7))]
        comments = [('k%d' % i, rnd.choice(['blocker', 'major', 'minor', 'nit']), rnd.random() < 0.6)
                    for i in range(rnd.randint(0, 3))]
        r = cr('a', reviews, comments)
        assert r == oracle('a', reviews, comments)
        seen.update(r['blocks'])
        ok += r['mergeable']
    assert seen == {'needs_two_approvals', 'changes_requested', 'open_blocking'} and ok > 1


def test_limits_accepted():
    reviews = [('r%02d' % i, 'approve') for i in range(32)]
    comments = [('k%02d' % i, 'blocker', True) for i in range(32)]
    assert len(cr('a', reviews, comments)['approvals']) == 32
    cr('a' * 24, [('b' * 24, 'approve')], [('c' * 24, 'nit', False)])


def err(exc, msg, a, r, c):
    with pytest.raises(exc) as e:
        cr(a, r, c)
    assert str(e.value) == msg


NM = 'name must be 1 to 24 lowercase identifier characters'
VM = "verdict must be 'approve', 'request_changes' or 'comment'"
SM = "severity must be 'blocker', 'major', 'minor' or 'nit'"
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')
NS = (None, 5, b'a', StrSub('a'))
R = [('b', 'approve')]
C = [('k', 'nit', True)]


def _pins(err):
    for bad in NS:
        err(T, 'name must be an exact string', bad, [], [])
        err(T, 'name must be an exact string', 'a', [(bad, 'approve')], [])
        err(T, 'name must be an exact string', 'a', [], [(bad, 'nit', True)])
    for bad in BAD:
        err(V, NM, bad, [], [])
        err(V, NM, 'a', [(bad, 'approve')], [])
        err(V, NM, 'a', [], [(bad, 'nit', True)])
    for bad in (None, (), 'ab', ListSub(R), {}):
        err(T, 'reviews must be an exact list', 'a', bad, [])
    err(V, 'review count must be at most 32', 'a', [('r%02d' % i, 'approve') for i in range(33)], [])
    for bad in (None, ['b', 'approve'], 'ba', TupleSub(('b', 'approve')), 5):
        err(T, 'each review must be an exact tuple', 'a', [bad], [])
    for bad in ((), ('b',), ('b', 'approve', 1)):
        err(V, 'each review must have 2 items', 'a', [bad], [])
    for bad in (None, 5, b'approve', StrSub('approve')):
        err(T, 'verdict must be an exact string', 'a', [('b', bad)], [])
    for bad in ('', 'Approve', 'approve ', 'lgtm', 'reject'):
        err(V, VM, 'a', [('b', bad)], [])
    for bad in (None, (), 'ab', ListSub(C), {}):
        err(T, 'comments must be an exact list', 'a', [], bad)
    err(V, 'comment count must be at most 32', 'a', [], [('k%02d' % i, 'nit', True) for i in range(33)])
    for bad in (None, ['k', 'nit', True], 'knt', TupleSub(('k', 'nit', True)), 5):
        err(T, 'each comment must be an exact tuple', 'a', [], [bad])
    for bad in ((), ('k', 'nit'), ('k', 'nit', True, 1)):
        err(V, 'each comment must have 3 items', 'a', [], [bad])
    for bad in (None, 5, b'nit', StrSub('nit')):
        err(T, 'severity must be an exact string', 'a', [], [('k', bad, True)])
    for bad in ('', 'Nit', 'nit ', 'critical', 'low'):
        err(V, SM, 'a', [], [('k', bad, True)])
    for bad in (None, 1, 0, 'True', [], 2):
        err(T, 'resolved must be an exact bool', 'a', [], [('k', 'nit', bad)])
    err(V, 'duplicate comment name', 'a', [], [('k', 'nit', True), ('j', 'nit', True), ('k', 'major', False)])


def _order(err):
    err(T, 'name must be an exact string', 5, 'x', 'y')
    err(V, NM, 'A', 'x', 'y')
    err(T, 'reviews must be an exact list', 'a', 'x', 'y')
    err(V, 'review count must be at most 32', 'a', [None] * 33, 'y')
    err(T, 'each review must be an exact tuple', 'a', [None, ('b',)], 'y')
    err(V, 'each review must have 2 items', 'a', [('b',), None], 'y')
    err(V, NM, 'a', [('A', 5)], 'y')
    err(T, 'name must be an exact string', 'a', [(5, 'zz')], 'y')
    err(T, 'verdict must be an exact string', 'a', [('b', 5)], 'y')
    err(V, VM, 'a', [('b', 'zz'), (5, 'x')], 'y')
    err(T, 'comments must be an exact list', 'a', R, 'y')
    err(V, 'comment count must be at most 32', 'a', R, [None] * 33)
    err(T, 'each comment must be an exact tuple', 'a', R, [None, ('k',)])
    err(V, 'each comment must have 3 items', 'a', R, [('k',), None])
    err(V, NM, 'a', R, [('A', 5, 5)])
    err(T, 'name must be an exact string', 'a', R, [(5, 'zz', 5)])
    err(T, 'severity must be an exact string', 'a', R, [('k', 5, 5)])
    err(V, SM, 'a', R, [('k', 'zz', 5)])
    err(T, 'resolved must be an exact bool', 'a', R, [('k', 'nit', 5), (5, 'nit', True)])
    err(V, 'duplicate comment name', 'a', R, [('k', 'nit', True), ('k', 'nit', True)])

def _collect(fn):
    out = []

    def rec(exc, msg, *a):
        out.append((exc, msg) + a)
    fn(rec)
    return out


@pytest.mark.parametrize('exc,msg,a,r,c', _collect(_pins))
def test_pin(exc, msg, a, r, c):
    err(exc, msg, a, r, c)


@pytest.mark.parametrize('exc,msg,a,r,c', _collect(_order))
def test_order(exc, msg, a, r, c):
    err(exc, msg, a, r, c)
