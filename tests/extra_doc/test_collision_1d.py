import random
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.collision_1d import collide_1d as col

T, V = TypeError, ValueError


def oracle(m1, x1, v1, m2, x2, v2, e):
    m1, x1, v1, m2, x2, v2, e = map(F, (m1, x1, v1, m2, x2, v2, e))
    if not v1 > v2:
        w = [v1, v2]
        t = pos = None
    else:
        # solve  m1*w1 + m2*w2 = P  and  w2 - w1 = e*(v1 - v2)  by Cramer's rule
        P = m1 * v1 + m2 * v2
        R = e * (v1 - v2)
        det = m1 * 1 - m2 * (-1)
        w1 = (P * 1 - m2 * R) / det
        w2 = (m1 * R - (-1) * P) / det
        w = [w1, w2]
        t = (x2 - x1) / (v1 - v2)
        pos = x1 + v1 * t
        assert x2 + v2 * t == pos            # both bodies are at the same place at that time
    ke = lambda a, b: (m1 * a ** 2 + m2 * b ** 2) / 2
    return {'collides': v1 > v2, 'time': t, 'impact_position': pos, 'velocities_after': w,
            'momentum_before': m1 * v1 + m2 * v2, 'momentum_after': m1 * w[0] + m2 * w[1],
            'energy_before': ke(v1, v2), 'energy_after': ke(*w), 'energy_lost': ke(v1, v2) - ke(*w)}


def test_hand_cases_exact():
    r = col(1, 0, 2, 1, 4, 0, 1)                    # equal masses, elastic: velocities swap
    assert r == {'collides': True, 'time': F(2), 'impact_position': F(4), 'velocities_after': [F(0), F(2)],
                 'momentum_before': F(2), 'momentum_after': F(2), 'energy_before': F(2), 'energy_after': F(2),
                 'energy_lost': F(0)}
    r = col(1, 0, 2, 1, 4, 0, 0)                    # sticky: both move at the mean velocity
    assert r['velocities_after'] == [F(1), F(1)] and r['energy_before'] == 2 and r['energy_after'] == 1
    assert r['energy_lost'] == 1
    r = col(3, -1, 4, 1, 3, -4, F(1, 2))
    r = col(3, -1, 4, 1, 3, -4, F(1, 2))             # hand-solved: P = 8, relative speed 8 -> w2 - w1 = 4, w1 = 1, w2 = 5
    assert r['time'] == F(1, 2) and r['impact_position'] == F(1) and r['velocities_after'] == [F(1), F(5)]
    assert r['momentum_before'] == 8 and r['energy_before'] == F(3 * 16 + 16, 2) and r['energy_after'] == F(3 + 25, 2)
    assert r['energy_lost'] == 18
    # moving apart or equal velocities: nothing happens
    r = col(1, 0, 1, 1, 5, 2, 1)
    assert r['collides'] is False and r['time'] is None and r['impact_position'] is None
    assert r['velocities_after'] == [F(1), F(2)] and r['energy_lost'] == 0
    assert col(2, 0, 3, 5, 1, 3, 1)['collides'] is False
    # a heavy body hits a light one at rest: the light one leaves at twice the speed (elastic)
    r = col(1000, 0, 1, 1, 10, 0, 1)
    assert r['velocities_after'][1] == F(2000, 1001)


def test_random_vs_oracle_and_laws():
    rnd = random.Random(577)
    hits = 0
    for _ in range(400):
        m1, m2 = F(rnd.randint(1, 50), rnd.randint(1, 5)), F(rnd.randint(1, 50), rnd.randint(1, 5))
        x1 = F(rnd.randint(-20, 20), rnd.randint(1, 4))
        x2 = x1 + F(rnd.randint(1, 20), rnd.randint(1, 4))
        v1, v2 = F(rnd.randint(-9, 9), rnd.randint(1, 3)), F(rnd.randint(-9, 9), rnd.randint(1, 3))
        e = F(rnd.randint(0, 6), 6)
        got = col(m1, x1, v1, m2, x2, v2, e)
        assert got == oracle(m1, x1, v1, m2, x2, v2, e)
        assert got['momentum_before'] == got['momentum_after']
        assert got['energy_lost'] >= 0
        if got['collides']:
            hits += 1
            a, b = got['velocities_after']
            assert b - a == e * (v1 - v2)
            assert (got['energy_lost'] == 0) == (e == 1)
    assert hits > 100


def err(f, exc, msg, *a):
    with pytest.raises(exc) as e:
        f(*a)
    assert str(e.value) == msg


OK = (1, 0, 1, 1, 5, 0, 1)


def with_(pos, val):
    a = list(OK)
    a[pos] = val
    return a


NAMES = ['m1', 'x1', 'v1', 'm2', 'x2', 'v2', 'restitution']


def test_pins_every_slot():
    for pos, nm in enumerate(NAMES):
        for bad in (True, 1.0, '1', None):
            err(col, T, nm + ' must be a nonbool int or Fraction', *with_(pos, bad))
        err(col, V, 'rational values must fit 32 bits', *with_(pos, F(1, 2 ** 32)))
        err(col, V, 'rational values must fit 32 bits', *with_(pos, 2 ** 32))
        err(col, V, 'rational values must fit 32 bits', *with_(pos, F(2 ** 32 + 1, 2 ** 32 + 3)))
    for pos in (0, 3):
        err(col, V, NAMES[pos] + ' must be greater than 0 and at most 1000000', *with_(pos, 0))
        err(col, V, NAMES[pos] + ' must be greater than 0 and at most 1000000', *with_(pos, -1))
        err(col, V, NAMES[pos] + ' must be greater than 0 and at most 1000000', *with_(pos, 1000001))
    for pos in (1, 2, 4, 5):
        for bad in (-1000001, 1000001):
            if pos == 4:
                continue
            err(col, V, NAMES[pos] + ' must be between -1000000 and 1000000', *with_(pos, bad))
    err(col, V, 'x2 must be between -1000000 and 1000000', *with_(4, 1000001))
    err(col, V, 'x2 must be between -1000000 and 1000000', *with_(4, -1000001))
    err(col, V, 'restitution must be between 0 and 1', *with_(6, F(-1, 2)))
    err(col, V, 'restitution must be between 0 and 1', *with_(6, F(3, 2)))
    err(col, V, 'x1 must be below x2', 1, 5, 1, 1, 5, 0, 1)
    err(col, V, 'x1 must be below x2', 1, 6, 1, 1, 5, 0, 1)


def test_edges_accepted():
    col(1000000, -1000000, 1000000, 1000000, 1000000, -1000000, 1)
    col(1, 0, 1, 1, 1, 0, 0)
    col(1, 0, 1, 1, 1, 0, 1)
    col(F(1, 2 ** 32 - 1), 0, 1, 1, 1, 0, F(1, 2 ** 32 - 1))
    col(F(2 ** 32 - 1, 2 ** 32 - 2), 0, 1, 1, 1, 0, 1)
    col(1, 0, 1, 1, 1, 0, F(2 ** 32 - 2, 2 ** 32 - 1))


def test_order_of_checks():
    err(col, T, 'm1 must be a nonbool int or Fraction', 1.0, 5, 'x', 0, 'y', 'z', 'w')
    err(col, V, 'm1 must be greater than 0 and at most 1000000', 0, 5, 1.5, 0, 1, 1, 1)
    err(col, T, 'v1 must be a nonbool int or Fraction', 1, 0, 1.5, 0, 0, 0, 0)       # types in argument order
    err(col, V, 'v2 must be between -1000000 and 1000000', 1, 5, 1, 1, 0, 10 ** 7, 1)   # range before x1 < x2
    err(col, V, 'x1 must be below x2', 1, 5, 1, 1, 0, 1, 1)


def test_exact_range_limits_on_each_side_for_positions_and_velocities():
    L = 1000000
    col(1, -L, 1, 1, 0, 0, 1)                      # x1 = -1e6
    col(1, 0, 1, 1, L, 0, 1)                       # x2 = 1e6
    col(1, 0, L, 1, 5, 0, 1)                       # v1 = 1e6
    col(1, 0, -L, 1, 5, -L, 1)                     # v1 = -1e6 (and v2 equal: no collision)
    col(1, 0, 1, 1, 5, L, 1)                       # v2 = 1e6
    col(1, 0, L, 1, 5, -L, 1)                      # both extremes at once
    err(col, V, 'x1 must be below x2', 1, L, 1, 1, L, 0, 1)      # x1 = 1e6 passes its range, then fails the order
    err(col, V, 'x1 must be below x2', 1, -L, 1, 1, -L, 0, 1)    # x2 = -1e6 passes its range, then fails the order
