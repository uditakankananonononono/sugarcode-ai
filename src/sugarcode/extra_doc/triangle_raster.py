"""Row 578, Rendering Engine (bounded scope: one exact step of a renderer): which pixels a triangle covers.

rasterize(width, height, a, b, c) takes a grid of width x height pixels, where pixel (x, y) has its sample point at
its centre (x + 1/2, y + 1/2), and a triangle with vertices a, b, c (each an (x, y) pair). It returns
  pixels   the covered pixels as (x, y) tuples, in row order (y first, then x);
  count    how many;
  area     the exact area of the triangle (a Fraction), whatever the vertex order.
A sample strictly inside covers its pixel. A sample exactly on an edge is decided by a fixed tie rule, so two
triangles that share an edge never cover a pixel twice and never leave a gap: the triangle is turned so its signed
area is positive, and for each edge p -> q with d = q - p, a sample on that edge counts when d.y < 0, or when
d.y == 0 and d.x > 0. A sample on a vertex is on two edges and needs both to count. Everything is exact (Fractions).
Caps: width and height are nonbool ints from 1 to 64; each vertex is a 2-item list or tuple of nonbool ints or
Fractions with 32-bit numerator and denominator, each coordinate from -1000 to 1000; the three vertices must not lie on
one line (zero area is an error).
Order of checks: width, height (type, then range), then the vertices a, b, c in order (shape, type, 32 bits, range,
x before y), then the zero-area check, and only then the scan.

NOT_CLAIMED: this is one coverage test, not a renderer. No shading, depth, blending, anti-aliasing, clipping to a
camera, texture, colour, or image output, and nothing about how a result looks. No clinical or wet-lab claim.
"""
from fractions import Fraction

LIM = 1000
SIZE = 64


def _dim(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be a nonbool int')
    if not 1 <= v <= SIZE:
        raise ValueError(what + ' must be between 1 and 64')
    return v


def _coord(v, what):
    if type(v) not in (int, Fraction):
        raise TypeError(what + ' must be a nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    if not -LIM <= f <= LIM:
        raise ValueError(what + ' must be between -1000 and 1000')
    return f


def _vertex(p, what):
    if type(p) not in (list, tuple) or len(p) != 2:
        raise TypeError(what + ' must be a list or tuple of two numbers')
    return (_coord(p[0], what + ' x'), _coord(p[1], what + ' y'))


def rasterize(width, height, a, b, c):
    w = _dim(width, 'width')
    h = _dim(height, 'height')
    p = _vertex(a, 'a')
    q = _vertex(b, 'b')
    r = _vertex(c, 'c')
    twice = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    if twice == 0:
        raise ValueError('the three vertices must not lie on one line')
    if twice < 0:
        q, r = r, q
    edges = [(p, q), (q, r), (r, p)]
    out = []
    half = Fraction(1, 2)
    for y in range(h):
        for x in range(w):
            sx, sy = x + half, y + half
            ok = True
            for s, t in edges:
                dx, dy = t[0] - s[0], t[1] - s[1]
                e = dx * (sy - s[1]) - dy * (sx - s[0])
                if e < 0 or (e == 0 and not (dy < 0 or (dy == 0 and dx > 0))):
                    ok = False
                    break
            if ok:
                out.append((x, y))
    return {'pixels': out, 'count': len(out), 'area': abs(twice) / 2}
