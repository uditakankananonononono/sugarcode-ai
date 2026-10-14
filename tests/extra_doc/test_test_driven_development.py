import random
import pytest
from sugarcode.extra_doc.test_driven_development import check_cycle as cc

T, V = TypeError, ValueError
PH = ['red', 'green', 'refactor']


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(log):
    legal = {('start', 'red'), ('red', 'green'), ('green', 'refactor'), ('green', 'red'), ('refactor', 'refactor'),
             ('refactor', 'red')}
    probs, cycles, state, before = [], 0, 'start', 0
    for i, (ph, p, f) in enumerate(log):
        if (state, ph) not in legal:
            probs.append((i, 'bad_order'))
        if ph == 'red' and not f >= 1:
            probs.append((i, 'red_without_failure'))
        if ph == 'green':
            if f > 0:
                probs.append((i, 'green_with_failure'))
            if state == 'red':
                cycles += 1
        if ph == 'refactor':
            if f > 0:
                probs.append((i, 'refactor_with_failure'))
            if p < before:
                probs.append((i, 'refactor_lost_tests'))
        state, before = ph, p
    return {'problems': sorted(probs), 'cycles': cycles, 'last_phase': None if state == 'start' else state}


def test_hand_cases():
    good = [('red', 1, 1), ('green', 2, 0), ('refactor', 2, 0), ('refactor', 3, 0), ('red', 3, 1), ('green', 4, 0)]
    assert cc(good) == {'problems': [], 'cycles': 2, 'last_phase': 'green'}
    assert cc([]) == {'problems': [], 'cycles': 0, 'last_phase': None}
    assert cc([('green', 1, 0)])['problems'] == [(0, 'bad_order')]
    assert cc([('refactor', 1, 0)])['problems'] == [(0, 'bad_order')]
    assert cc([('red', 1, 0)])['problems'] == [(0, 'red_without_failure')]
    assert cc([('red', 0, 1), ('red', 0, 1)])['problems'] == [(1, 'bad_order')]
    assert cc([('red', 0, 1), ('green', 0, 1)])['problems'] == [(1, 'green_with_failure')]
    assert cc([('red', 0, 1), ('green', 1, 0), ('green', 1, 0)])['problems'] == [(2, 'bad_order')]
    assert cc([('red', 0, 1), ('green', 1, 0), ('refactor', 1, 1)])['problems'] == [(2, 'refactor_with_failure')]
    assert cc([('red', 0, 1), ('green', 5, 0), ('refactor', 4, 0)])['problems'] == [(2, 'refactor_lost_tests')]
    assert cc([('red', 0, 1), ('green', 5, 0), ('refactor', 5, 0)])['problems'] == []              # equal passed is fine
    assert cc([('red', 0, 1), ('green', 5, 0), ('refactor', 5, 0), ('green', 5, 0)])['problems'] == [(3, 'bad_order')]
    assert cc([('red', 0, 1), ('green', 5, 0), ('refactor', 4, 2)])['problems'] == [
        (2, 'refactor_lost_tests'), (2, 'refactor_with_failure')]
    assert cc([('red', 0, 1), ('green', 5, 0), ('red', 5, 1), ('green', 6, 0)])['cycles'] == 2
    assert cc([('red', 0, 1), ('green', 5, 0), ('refactor', 5, 0), ('green', 5, 0)])['cycles'] == 1


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(6870 + part)
    seen, clean = set(), 0
    for _ in range(60):
        if rnd.random() < 0.5:
            log, p = [], 0
            for _ in range(rnd.randint(1, 3)):
                log.append(('red', p, rnd.randint(1, 2)))
                p += rnd.randint(0, 2)
                log.append(('green', p, 0))
                for _ in range(rnd.randint(0, 2)):
                    log.append(('refactor', p, 0))
            if rnd.random() < 0.3:
                i = rnd.randrange(len(log))
                log[i] = (rnd.choice(PH), rnd.randint(0, 3), rnd.randint(0, 2))
        else:
            log = [(rnd.choice(PH), rnd.randint(0, 3), rnd.randint(0, 2)) for _ in range(rnd.randint(0, 6))]
        r = cc(log)
        assert r == oracle(log)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert len(seen) >= 4 and clean > 5


def test_every_short_log_matches_oracle():
    import itertools
    cells = [(ph, p, f) for ph in PH for p in (0, 1) for f in (0, 1)]
    for n in range(0, 4):
        for log in itertools.product(cells, repeat=n):
            assert cc(list(log)) == oracle(list(log))


def test_limits_accepted():
    log = [('red', 1000, 1000)] + [('green', 1000, 0)] + [('refactor', 1000, 0)] * 58
    assert len(log) == 60 and cc(log) == {'problems': [], 'cycles': 1, 'last_phase': 'refactor'}
    assert cc([('red', 0, 1)])['last_phase'] == 'red'


def err(exc, msg, log):
    with pytest.raises(exc) as e:
        cc(log)
    assert str(e.value) == msg


PM = "phase must be 'red', 'green' or 'refactor'"
CT = 'count must be an exact int'
CR = 'count must be between 0 and 1000'


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'log must be an exact list', bad)
    err(V, 'entry count must be at most 60', [('red', 0, 1)] * 61)
    for bad in (None, ['red', 0, 1], 'red', TupleSub(('red', 0, 1)), 5):
        err(T, 'each entry must be an exact tuple', [bad])
    for bad in ((), ('red', 0), ('red', 0, 1, 2)):
        err(V, 'each entry must have 3 items', [bad])
    for bad in (None, 5, b'red', StrSub('red')):
        err(T, 'phase must be an exact string', [(bad, 0, 1)])
    for bad in ('', 'Red', 'red ', 'refactoring', 'blue', 'é'):
        err(V, PM, [(bad, 0, 1)])
    for bad in (None, 1.0, '1', True, False, IntSub(1), b'1'):
        err(T, CT, [('red', bad, 1)])
        err(T, CT, [('red', 0, bad)])
    for bad in (-1, 1001, 2 ** 40):
        err(V, CR, [('red', bad, 1)])
        err(V, CR, [('red', 0, bad)])


def _order(err):
    err(T, 'log must be an exact list', 'x')
    err(V, 'entry count must be at most 60', [None] * 61)
    err(T, 'each entry must be an exact tuple', [None, ('a',)])
    err(V, 'each entry must have 3 items', [('a',), None])
    err(T, 'phase must be an exact string', [(5, 'x', 'x')])
    err(V, PM, [('zz', 'x', 'x')])
    err(T, CT, [('red', 'x', 2 ** 40)])
    err(V, CR, [('red', 2 ** 40, 'x')])
    err(T, CT, [('red', 0, 'x'), ('zz', 0, 0)])
    err(V, PM, [('zz', 0, 0), (5, 0, 0)])


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
