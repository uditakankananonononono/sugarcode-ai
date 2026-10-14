import random
import pytest
from sugarcode.extra_doc.training_design import check_programs as cp

T, V = TypeError, ValueError


class StrSub(str):
    pass


class ListSub(list):
    pass


class TupleSub(tuple):
    pass


class IntSub(int):
    pass


def oracle(programs):
    # written from the stated rule: under 2 delivered hours is too brief; under 70 pass is low
    probs = []
    for i, (_, h, p) in enumerate(programs):
        if h < 2:
            probs.append((i, 'too_brief'))
        if p < 70:
            probs.append((i, 'low_pass'))
    return {'problems': sorted(probs), 'modules': sorted({m for m, _, _ in programs}), 'total': len(programs)}


DISCLAIMER = ('NOT_CLAIMED: this checks supplied program numbers against two delivery bars. It does not say '
              'capabilities develop, that 2 hours or 70 are the right bars, or that anyone learned. No clinical '
              'or wet-lab claim.')


def test_disclaimer_pinned():
    import sugarcode.extra_doc.training_design as mod
    assert ' '.join(mod.__doc__.split()).split('NOT_CLAIMED: ', 1)[1] == DISCLAIMER.removeprefix('NOT_CLAIMED: ')


def test_hand_cases():
    assert cp([]) == {'problems': [], 'modules': [], 'total': 0}
    assert cp([('a', 2, 70)]) == {'problems': [], 'modules': ['a'], 'total': 1}
    assert cp([('a', 1, 70)])['problems'] == [(0, 'too_brief')]
    assert cp([('a', 0, 100)])['problems'] == [(0, 'too_brief')]
    assert cp([('a', 40, 70)])['problems'] == []
    assert cp([('a', 2, 69)])['problems'] == [(0, 'low_pass')]
    assert cp([('a', 2, 0)])['problems'] == [(0, 'low_pass')]
    assert cp([('a', 1, 69)])['problems'] == [(0, 'low_pass'), (0, 'too_brief')]
    assert cp([('a', 1, 69), ('b', 5, 90), ('c', 0, 0)])['problems'] == [
        (0, 'low_pass'), (0, 'too_brief'), (2, 'low_pass'), (2, 'too_brief')]
    assert cp([('b', 5, 90), ('a', 5, 90)]) == {'problems': [], 'modules': ['a', 'b'], 'total': 2}


@pytest.mark.parametrize('part', range(8))
def test_random_vs_oracle(part):
    rnd = random.Random(4770 + part)
    seen, clean = set(), 0
    for _ in range(60):
        programs = []
        for _ in range(rnd.randint(0, 9)):
            programs.append((rnd.choice(('m1', 'm2', 'm3')),
                             rnd.choice((0, 1, 2, 40, rnd.randint(0, 40))),
                             rnd.choice((0, 69, 70, 100, rnd.randint(0, 100)))))
        r = cp(programs)
        assert r == oracle(programs)
        seen.update(c for _, c in r['problems'])
        clean += not r['problems']
    assert seen == {'too_brief', 'low_pass'} and clean >= 2


def test_limits_accepted():
    programs = [('m%02d' % k, 2, 70) for k in range(40)]
    r = cp(programs)
    assert r['total'] == 40 and r['problems'] == []
    cp([('a' * 24, 40, 100)])
    cp([('a', 0, 0)])


def err(exc, msg, programs):
    with pytest.raises(exc) as e:
        cp(programs)
    assert str(e.value) == msg


MM = 'module must be 1 to 24 lowercase identifier characters'
NS = (None, 5, b'a', StrSub('a'))
NI = (None, '5', 5.0, True, IntSub(5))
BAD = ('', 'A', '1a', 'a-b', 'a' * 25, 'a\n', 'é', '_a', 'aé', 'ａ')


def _pins(err):
    for bad in (None, (), 'ab', ListSub([]), {}):
        err(T, 'programs must be an exact list', bad)
    err(V, 'program count must be at most 40', [('m', 2, 70)] * 41)
    for bad in (None, ['m', 2, 70], 'ab', TupleSub(('m', 2, 70)), 5):
        err(T, 'each program must be an exact tuple', [bad])
    for bad in ((), ('m', 2), ('m', 2, 70, 0)):
        err(V, 'each program must have 3 items', [bad])
    for bad in NS:
        err(T, 'module must be an exact string', [(bad, 2, 70)])
    for bad in BAD:
        err(V, MM, [(bad, 2, 70)])
    for bad in NI:
        err(T, 'hours must be an exact integer', [('m', bad, 70)])
        err(T, 'pass_rate must be an exact integer', [('m', 2, bad)])
    for bad in (-1, 41, -100, 10**9):
        err(V, 'hours must be 0 to 40', [('m', bad, 70)])
    for bad in (-1, 101, -100, 10**9):
        err(V, 'pass_rate must be 0 to 100', [('m', 2, bad)])


def _order(err):
    err(T, 'programs must be an exact list', 'x')
    err(V, 'program count must be at most 40', [None] * 41)
    err(T, 'each program must be an exact tuple', [None, ('m',)])
    err(V, 'each program must have 3 items', [('m',), None])
    err(T, 'module must be an exact string', [(5, -1, -1)])
    err(V, MM, [('A', -1, -1)])
    err(T, 'hours must be an exact integer', [('m', '0', -1)])
    err(V, 'hours must be 0 to 40', [('m', -1, -1)])
    err(T, 'pass_rate must be an exact integer', [('m', 0, '0')])
    err(V, 'pass_rate must be 0 to 100', [('m', 0, -1)])
    err(T, 'module must be an exact string', [('m', 2, 70), (5, 2, 70)])
    err(T, 'hours must be an exact integer', [('m', 2, 70), ('m', '0', 70)])
    err(T, 'pass_rate must be an exact integer', [('m', 2, 70), ('m', 2, '0')])


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
