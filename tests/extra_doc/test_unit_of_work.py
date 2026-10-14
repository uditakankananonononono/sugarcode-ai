import random
import pytest
from sugarcode.extra_doc.unit_of_work import commit_unit_of_work as uow

T, V = TypeError, ValueError


class StrSub(str):
    pass


class IntSub(int):
    pass


class DictSub(dict):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


def oracle(state, changes):
    # per key: walk that key's own changes, remembering the first broken rule (by position) and the net outcome
    first_err = None
    net = {}
    for key in {c[1] for c in changes}:
        present = key in state
        value = state.get(key)
        for idx, (a, k, v) in enumerate(changes):
            if k != key:
                continue
            msg = None
            if a == 'new':
                if present:
                    msg = 'new: key already exists'
                else:
                    present, value = True, v
            elif not present:
                msg = a + ': key does not exist'
            elif a == 'dirty':
                value = v
            elif v != 0:
                msg = 'removed: value must be 0'
            else:
                present, value = False, None
            if msg:
                if first_err is None or idx < first_err[0]:
                    first_err = (idx, msg)
                break
        net[key] = (present, value)
    if first_err:
        return ('error', first_err[1])
    final = dict(state)
    for k, (p, v) in net.items():
        if p:
            final[k] = v
        else:
            final.pop(k, None)
    ins = sorted(k for k in final if k not in state)
    upd = sorted(k for k in final if k in state and final[k] != state[k])
    dele = sorted(k for k in state if k not in final)
    st = [('insert', k, final[k]) for k in ins] + [('update', k, final[k]) for k in upd] + [('delete', k, 0) for k in dele]
    return {'state': sorted(final.items()), 'inserts': ins, 'updates': upd, 'deletes': dele, 'statements': st}


def run(state, changes):
    try:
        return uow(state, changes)
    except ValueError as e:
        return ('error', str(e))


def test_hand_cases():
    r = uow({'a': 1, 'b': 2}, [('new', 'c', 3), ('dirty', 'a', 10), ('removed', 'b', 0)])
    assert r == {'state': [('a', 10), ('c', 3)], 'inserts': ['c'], 'updates': ['a'], 'deletes': ['b'],
                 'statements': [('insert', 'c', 3), ('update', 'a', 10), ('delete', 'b', 0)]}
    r = uow({}, [('new', 'a', 1), ('removed', 'a', 0)])               # cancels out
    assert r == {'state': [], 'inserts': [], 'updates': [], 'deletes': [], 'statements': []}
    r = uow({'a': 1}, [('removed', 'a', 0), ('new', 'a', 5)])         # replaced
    assert r['updates'] == ['a'] and r['statements'] == [('update', 'a', 5)] and r['inserts'] == [] and r['deletes'] == []
    r = uow({'a': 1}, [('dirty', 'a', 1)])                             # same value: no statement
    assert r == {'state': [('a', 1)], 'inserts': [], 'updates': [], 'deletes': [], 'statements': []}
    r = uow({'a': 1}, [('dirty', 'a', 2), ('dirty', 'a', 1)])
    assert r['updates'] == [] and r['statements'] == []
    r = uow({}, [('new', 'a', 1), ('dirty', 'a', 9)])
    assert r['statements'] == [('insert', 'a', 9)]
    r = uow({'z': 0, 'y': 0}, [('new', 'b', 1), ('new', 'a', 2), ('dirty', 'z', 1), ('dirty', 'y', 1)])
    assert [s[1] for s in r['statements']] == ['a', 'b', 'y', 'z']
    r = uow({'b': 1, 'a': 1}, [('removed', 'b', 0), ('removed', 'a', 0)])
    assert r['statements'] == [('delete', 'a', 0), ('delete', 'b', 0)]
    st = {'a': 1}
    ch = [('dirty', 'a', 2)]
    uow(st, ch)
    assert st == {'a': 1} and ch == [('dirty', 'a', 2)]
    # first broken rule wins and nothing is committed
    for chs, msg in (([('new', 'a', 1)], 'new: key already exists'), ([('dirty', 'q', 1)], 'dirty: key does not exist'),
                     ([('removed', 'q', 0)], 'removed: key does not exist'), ([('removed', 'a', 1)], 'removed: value must be 0'),
                     ([('removed', 'a', 0), ('dirty', 'a', 1)], 'dirty: key does not exist'),
                     ([('removed', 'a', 0), ('removed', 'a', 0)], 'removed: key does not exist'),
                     ([('new', 'b', 1), ('new', 'b', 2)], 'new: key already exists'),
                     ([('dirty', 'q', 1), ('new', 'a', 1)], 'dirty: key does not exist'),
                     ([('new', 'a', 1), ('dirty', 'q', 1)], 'new: key already exists')):
        with pytest.raises(V) as e:
            uow({'a': 1}, chs)
        assert str(e.value) == msg


def test_random_vs_per_key_oracle():
    rnd = random.Random(670)
    errs = oks = 0
    for _ in range(800):
        keys = ['a', 'b', 'c', 'd']
        state = {k: rnd.randint(0, 2) for k in rnd.sample(keys, rnd.randint(0, 4))}
        present = set(state)
        changes = []
        for _ in range(rnd.randint(1, 6)):
            k = rnd.choice(keys)
            if rnd.random() < 0.85:                              # mostly a legal change for the current picture
                a = rnd.choice(['dirty', 'removed']) if k in present else 'new'
            else:
                a = rnd.choice(['new', 'dirty', 'removed'])
            v = 0 if a == 'removed' and rnd.random() < 0.9 else rnd.choice([0, 1, 2])
            changes.append((a, k, v))
            if a == 'new':
                present.add(k)
            elif a == 'removed':
                present.discard(k)
        got = run(state, changes)
        assert got == oracle(state, changes)
        if isinstance(got, tuple):
            errs += 1
        else:
            oks += 1
    assert errs > 100 and oks > 100


def test_limits_accepted():
    uow({'k%02d' % i: 0 for i in range(32)}, [('dirty', 'k00', 1)])
    uow({}, [('new', 'k%02d' % i, i) for i in range(64)])
    uow({'a': 1000000}, [('dirty', 'a', -1000000)])
    uow({'a' * 24: 1}, [('removed', 'a' * 24, 0)])
    assert len(uow({}, [('new', 'k%02d' % i, 0) for i in range(32)] + [('removed', 'k%02d' % i, 0) for i in range(32)])['statements']) == 0


def err(exc, msg, state, changes):
    with pytest.raises(exc) as e:
        uow(state, changes)
    assert str(e.value) == msg


OKS = {'a': 1}
OKC = [('dirty', 'a', 2)]


def test_pins():
    for bad in (None, [], (), DictSub(), 'x'):
        err(T, 'state must be an exact dict', bad, OKC)
    err(V, 'state must have at most 32 keys', {'k%02d' % i: 0 for i in range(33)}, OKC)
    for bad in (None, 5, b'a', StrSub('a')):
        err(T, 'key must be an exact string', {bad: 1}, OKC)
        err(T, 'key must be an exact string', OKS, [('new', bad, 1)])
    for bad in ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a'):
        err(V, 'key must be 1 to 24 lowercase identifier characters', {bad: 1}, OKC)
        err(V, 'key must be 1 to 24 lowercase identifier characters', OKS, [('new', bad, 1)])
    for bad in (True, False, 1.0, '1', None, IntSub(1)):
        err(T, 'value must be a nonbool int', {'a': bad}, OKC)
        err(T, 'value must be a nonbool int', OKS, [('dirty', 'a', bad)])
    for bad in (1000001, -1000001):
        err(V, 'value must be between -1000000 and 1000000', {'a': bad}, OKC)
        err(V, 'value must be between -1000000 and 1000000', OKS, [('dirty', 'a', bad)])
    for bad in (None, (), 'ab', ListSub(OKC), {}):
        err(T, 'changes must be an exact list', OKS, bad)
    err(V, 'change count must be between 1 and 64', OKS, [])
    err(V, 'change count must be between 1 and 64', OKS, [('dirty', 'a', 1)] * 65)
    for bad in (None, ['dirty', 'a', 1], 'abc', TupleSub(('dirty', 'a', 1)), 5):
        err(T, 'each change must be an exact tuple', OKS, [bad])
    for bad in ((), ('dirty',), ('dirty', 'a'), ('dirty', 'a', 1, 1)):
        err(V, 'each change must have 3 items', OKS, [bad])
    for bad in (None, 5, b'new', StrSub('new')):
        err(T, 'action must be an exact string', OKS, [(bad, 'a', 1)])
    for bad in ('', 'New', 'insert', 'update', 'delete', 'new ', 'remove'):
        err(V, "action must be 'new', 'dirty' or 'removed'", OKS, [(bad, 'a', 1)])


def test_order_of_checks():
    err(T, 'state must be an exact dict', 'x', 'y')
    err(V, 'state must have at most 32 keys', {'k%02d' % i: 'x' for i in range(33)}, 'y')
    err(T, 'key must be an exact string', {5: 'x', 'A': 1}, 'y')
    err(V, 'key must be 1 to 24 lowercase identifier characters', {'A': 'x', 5: 1}, 'y')
    err(T, 'value must be a nonbool int', {'a': 1.5, 'b': 10 ** 9}, 'y')
    err(V, 'value must be between -1000000 and 1000000', {'a': 10 ** 9, 'b': 1.5}, 'y')
    err(T, 'changes must be an exact list', OKS, 'y')
    err(V, 'change count must be between 1 and 64', OKS, [None] * 65)
    err(T, 'each change must be an exact tuple', OKS, [None, ('a',)])
    err(V, 'each change must have 3 items', OKS, [('a',), None])
    err(T, 'action must be an exact string', OKS, [(5, 5, 5), ('zz', 'A', 'x')])
    err(V, "action must be 'new', 'dirty' or 'removed'", OKS, [('zz', 5, 5)])
    err(T, 'key must be an exact string', OKS, [('new', 5, 5)])
    err(V, 'key must be 1 to 24 lowercase identifier characters', OKS, [('new', 'A', 'x')])
    err(T, 'value must be a nonbool int', OKS, [('new', 'a', 'x')])
    err(V, 'value must be between -1000000 and 1000000', OKS, [('new', 'a', 10 ** 9)])
    # every change is validated before any rule is applied
    err(V, "action must be 'new', 'dirty' or 'removed'", OKS, [('new', 'a', 1), ('zz', 'a', 1)])
    err(T, 'each change must be an exact tuple', OKS, [('dirty', 'zz', 1), None])
