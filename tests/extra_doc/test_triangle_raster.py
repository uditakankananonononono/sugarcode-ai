import itertools
import random
from decimal import Decimal
from fractions import Fraction as F
import pytest
from sugarcode.extra_doc.triangle_raster import rasterize as ras

T, V = TypeError, ValueError
EPS = F(1, 10 ** 40)


def cross(o, p, q):
    return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])


def inside_strict(pt, a, b, c):
    # the point is strictly inside when it is on the same strict side of all three edges (by sub-triangle areas)
    s = [cross(a, b, pt), cross(b, c, pt), cross(c, a, pt)]
    return all(v > 0 for v in s) or all(v < 0 for v in s)


def oracle(w, h, a, b, c):
    a, b, c = [(F(p[0]), F(p[1])) for p in (a, b, c)]
    out = []
    for y in range(h):
        for x in range(w):
            # a sample on an edge is moved by (EPS, EPS squared); it counts when the moved point is strictly inside
            pt = (x + F(1, 2) + EPS, y + F(1, 2) + EPS * EPS)
            if inside_strict(pt, a, b, c):
                out.append((x, y))
    return out


def test_hand_cases():
    r = ras(4, 4, (0, 0), (4, 0), (0, 4))           # centres with x + y < 3 are inside; x + y == 3 is the hypotenuse, left out
    assert r['pixels'] == [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2)]
    assert r['count'] == 6 and r['area'] == 8 and type(r['area']) is F
    assert ras(4, 4, (0, 0), (2, 0), (0, 2)) == {'pixels': [(0, 0)], 'count': 1, 'area': F(2)}
    # the other diagonal: the hypotenuse samples are included on that side
    r = ras(4, 4, (4, 0), (4, 4), (0, 4))
    assert r['pixels'] == [(3, 0), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2), (0, 3), (1, 3), (2, 3), (3, 3)]
    assert r['area'] == 8
    # a tiny triangle that misses every centre
    assert ras(3, 3, (0, 0), (F(1, 4), 0), (0, F(1, 4))) == {'pixels': [], 'count': 0, 'area': F(1, 32)}
    # a triangle around one centre
    assert ras(3, 3, (1, 1), (2, 1), (F(3, 2), 2))['pixels'] == [(1, 1)]
    assert type(ras(2, 2, (0, 0), (2, 0), (0, 2))['pixels'][0]) is tuple


def test_random_vs_oracle():
    rnd = random.Random(578)
    nonempty = ties = 0
    for _ in range(400):
        w, h = rnd.randint(1, 7), rnd.randint(1, 7)
        d = rnd.choice([1, 2, 2, 4])
        pts = [(F(rnd.randint(-4 * d, 9 * d), d), F(rnd.randint(-4 * d, 9 * d), d)) for _ in range(3)]
        if cross(*pts) == 0:
            with pytest.raises(V, match='not lie on one line'):
                ras(w, h, *pts)
            continue
        r = ras(w, h, *pts)
        want = oracle(w, h, *pts)
        assert r['pixels'] == want
        assert r['count'] == len(want) and r['area'] == abs(cross(*pts)) / 2
        nonempty += bool(want)
        for perm in itertools.permutations(pts):    # vertex order and winding do not matter
            assert ras(w, h, *perm)['pixels'] == want
    assert nonempty > 150


def test_sample_exactly_on_edges_follow_the_tie_rule():
    # centre (1/2, 1/2) is on each edge in turn
    tri = [(0, 0), (1, 1), (0, 2)]                   # edge (0,0)-(1,1) passes through (1/2, 1/2)
    assert ras(1, 2, *tri)['pixels'] == oracle(1, 2, *tri)
    tri2 = [(0, F(1, 2)), (3, F(1, 2)), (1, 3)]       # horizontal edge through the centres of row 0
    assert ras(3, 3, *tri2)['pixels'] == oracle(3, 3, *tri2)
    tri3 = [(0, F(1, 2)), (3, F(1, 2)), (1, -2)]      # the same edge, flipped to the other side
    assert ras(3, 3, *tri3)['pixels'] == oracle(3, 3, *tri3)
    # exactly one of the two triangles on either side of a shared horizontal edge owns row 0
    up = ras(3, 3, (0, F(1, 2)), (3, F(1, 2)), (1, 3))['pixels']
    dn = ras(3, 3, (0, F(1, 2)), (3, F(1, 2)), (1, -2))['pixels']
    assert not set(up) & set(dn)
    assert {p for p in up + dn if p[1] == 0} == {(x, 0) for x in range(3)}
    # a sample on a vertex belongs to the triangle only when it passes both edges; here it is on three-way ties
    for tri in ([(F(1, 2), F(1, 2)), (3, 0), (0, 3)], [(F(1, 2), F(1, 2)), (3, 3), (0, 4)],
                [(F(1, 2), F(1, 2)), (-2, 1), (1, -3)]):
        assert ras(4, 4, *tri)['pixels'] == oracle(4, 4, *tri)


def test_shared_edges_never_overlap_and_never_leave_gaps():
    rnd = random.Random(5781)
    for _ in range(120):
        w, h = rnd.randint(1, 8), rnd.randint(1, 8)
        d = rnd.choice([1, 2])
        px = F(rnd.randint(1, 2 * w * d - 1), 2 * d)           # an interior point, often a half-integer: ties abound
        py = F(rnd.randint(1, 2 * h * d - 1), 2 * d)
        if rnd.random() < 0.5:
            px, py = F(rnd.randint(1, w - 1 if w > 1 else 1)), F(rnd.randint(1, h - 1 if h > 1 else 1))
        corners = [(0, 0), (w, 0), (w, h), (0, h)]
        seen = []
        for i in range(4):
            tri = (corners[i], corners[(i + 1) % 4], (px, py))
            if cross(*tri) == 0:
                continue
            seen += ras(w, h, *tri)['pixels']
        assert sorted(seen, key=lambda t: (t[1], t[0])) == [(x, y) for y in range(h) for x in range(w)]    # each pixel exactly once
    for w, h in ((1, 1), (5, 3), (64, 64)):
        a = ras(w, h, (0, 0), (w, 0), (w, h))['pixels']
        b = ras(w, h, (0, 0), (w, h), (0, h))['pixels']
        assert len(a) + len(b) == w * h and not set(a) & set(b)


def test_clipping_negative_and_far_vertices():
    tri = [(-1000, -1000), (1000, -1000), (0, 1000)]
    assert ras(5, 5, *tri)['pixels'] == oracle(5, 5, *tri)
    tri = [(-3, -3), (F(1, 2), 40), (F(7, 2), 1)]
    assert ras(4, 4, *tri)['pixels'] == oracle(4, 4, *tri)
    assert ras(2, 2, (10, 10), (20, 10), (10, 20))['pixels'] == []
    r = ras(3, 2, (-1, -1), (5, -1), (-1, 5))
    assert r['pixels'] == [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)]     # (2, 1) is on the hypotenuse x + y = 4
    assert r['area'] == 18


def test_widths_nonbool_and_32_bit_boundaries():
    assert ras(1, 1, (0, 0), (2, 0), (0, 2))['count'] == 1
    assert ras(64, 64, (0, 0), (64, 0), (0, 64))['count'] == 64 * 63 // 2
    for bad in (True, 2.0, F(2), '2', None, Decimal(2)):
        with pytest.raises(T, match='^width must be a nonbool int$'):
            ras(bad, 2, (0, 0), (1, 0), (0, 1))
        with pytest.raises(T, match='^height must be a nonbool int$'):
            ras(2, bad, (0, 0), (1, 0), (0, 1))
    for bad in (0, -1, 65):
        with pytest.raises(V, match='^width must be between 1 and 64$'):
            ras(bad, 2, (0, 0), (1, 0), (0, 1))
        with pytest.raises(V, match='^height must be between 1 and 64$'):
            ras(2, bad, (0, 0), (1, 0), (0, 1))
    for bad in (True, 1.5, Decimal(1), '1', None):
        with pytest.raises(T, match='^a x must be a nonbool int or Fraction$'):
            ras(2, 2, (bad, 0), (1, 0), (0, 1))
    with pytest.raises(T, match='^c y must be a nonbool int or Fraction$'):
        ras(2, 2, (0, 0), (1, 0), (0, True))
    ok = ras(2, 2, (0, 0), (F(2 ** 32 - 1, 2 ** 23), 0), (0, F(1, 2 ** 32 - 1)))    # 32-bit numerator and denominator
    assert ok['area'] == F(2 ** 32 - 1, 2 ** 23) * F(1, 2 ** 32 - 1) / 2
    for bad in (F(2 ** 32 + 1, 2 ** 23 + 1), F(1, 2 ** 32), F(1, 2 ** 32 + 1)):
        assert bad.numerator.bit_length() > 32 or bad.denominator.bit_length() > 32
        with pytest.raises(V, match='^rational values must fit 32 bits$'):
            ras(2, 2, (0, 0), (1, 0), (0, bad))
    # range edges: 1000 passes, a hair over fails, both signs, each coordinate
    ras(2, 2, (-1000, 1000), (1000, -1000), (0, 5))
    ras(2, 2, (-1000, -1000), (1000, 1000), (0, 5))
    for v in (1001, -1001, F(2001, 2), F(-2001, 2)):
        with pytest.raises(V, match='^a x must be between -1000 and 1000$'):
            ras(2, 2, (v, 0), (1, 0), (0, 1))
        with pytest.raises(V, match='^b y must be between -1000 and 1000$'):
            ras(2, 2, (0, 0), (1, v), (0, 1))
    for bad in ((0,), (0, 0, 0), 'ab', {0: 1, 1: 2}, None, 5):
        with pytest.raises(T, match='^a must be a list or tuple of two numbers$'):
            ras(2, 2, bad, (1, 0), (0, 1))
    ras(2, 2, [0, 0], [2, 0], [0, 2])
    with pytest.raises(T, match='^c must be a list or tuple of two numbers$'):
        ras(2, 2, (0, 0), (1, 0), (0, 1, 2))


def test_check_order_and_no_scan_before_checks():
    A, B, C = (0, 0), (1, 0), (0, 1)
    with pytest.raises(T, match='^width'):
        ras(True, 0, 'x', 'y', 'z')
    with pytest.raises(V, match='^width'):
        ras(0, True, 'x', 'y', 'z')
    with pytest.raises(T, match='^height'):
        ras(2, 1.5, 'x', 'y', 'z')
    with pytest.raises(V, match='^height'):
        ras(2, 0, 'x', 'y', 'z')
    with pytest.raises(T, match='^a must'):
        ras(2, 2, 'x', (5000, 0), (0, 0, 0))
    with pytest.raises(T, match='^a x'):
        ras(2, 2, (1.5, 5000), (5000, 0), 'z')
    with pytest.raises(V, match='^a x must be between'):
        ras(2, 2, (5000, 1.5), 'y', 'z')
    with pytest.raises(V, match='^a y must be between'):
        ras(2, 2, (0, 5000), (1.5, 0), 'z')
    with pytest.raises(T, match='^b must'):
        ras(2, 2, A, 'y', 'z')
    with pytest.raises(V, match='^b x must be between'):
        ras(2, 2, A, (5000, 1.5), 'z')
    with pytest.raises(T, match='^c must'):
        ras(2, 2, A, B, 'z')
    with pytest.raises(V, match='^c y must be between'):
        ras(2, 2, A, B, (0, 5000))
    with pytest.raises(V, match='^c x must be between'):
        ras(2, 2, A, B, (-5000, 5000))
    with pytest.raises(V, match='^rational values must fit 32 bits$'):
        ras(2, 2, (F(1, 2 ** 32), 5000), B, C)       # the 32-bit check comes before the range check
    with pytest.raises(V, match='^rational values must fit 32 bits$'):
        ras(2, 2, (0, F(1, 2 ** 32)), (5000, 0), C)  # x passes, y fails width, before b is looked at
    # the zero-area check comes after every vertex check and before any scan
    with pytest.raises(V, match='^c x must be between'):
        ras(2, 2, (0, 0), (1, 0), (5000, 0))
    with pytest.raises(V, match='^the three vertices must not lie on one line$'):
        ras(64, 64, (0, 0), (1, 1), (2, 2))
    with pytest.raises(V, match='^the three vertices must not lie on one line$'):
        ras(1, 1, (3, 3), (3, 3), (0, 1))
    with pytest.raises(V, match='^the three vertices must not lie on one line$'):
        ras(2, 2, (F(1, 3), F(1, 3)), (F(2, 3), F(2, 3)), (1, 1))
    with pytest.raises(V, match='^the three vertices must not lie on one line$'):
        ras(2, 2, (0, 0), (5, 0), (-7, 0))


def test_short_horizontal_edges_with_samples_on_them():
    # a horizontal edge through a sample row, with dx of small size and either sign: 1/2, 1, -1/2, -1
    for dx in (F(1, 2), F(1), F(-1, 2), F(-1), F(1, 4), F(-1, 4)):
        for apex in ((F(3, 2), 3), (F(3, 2), -2)):
            tri = [(1, F(3, 2)), (1 + dx, F(3, 2)), apex]
            want = oracle(4, 4, *tri)
            assert ras(4, 4, *tri)['pixels'] == want
    # hand case: base (1, 3/2)-(2, 3/2) with the apex above (y larger). The centre (3/2, 3/2) is on the base and the
    # apex (3/2, 3) is straight above it, so that centre is inside only for the orientation that includes this edge
    with_apex_up = ras(4, 4, (1, F(3, 2)), (2, F(3, 2)), (F(3, 2), 3))['pixels']
    with_apex_down = ras(4, 4, (1, F(3, 2)), (2, F(3, 2)), (F(3, 2), 0))['pixels']
    assert (1, 1) in with_apex_up and (1, 1) not in with_apex_down
    assert with_apex_up == [(1, 1), (1, 2)] and with_apex_down == [(1, 0)]
