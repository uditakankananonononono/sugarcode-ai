"""Semidefinite Programming - exact optimum of a 2x2 SDP, reported as a + b*sqrt(m).

Pure function over caller data. No retrieval, no network, no clock, no floats, no solver
library, no randomness. Problem over the symmetric matrix X = [[x, y], [y, z]]:
minimize <C, X> = c11*x + 2*c12*y + c22*z subject to X positive semidefinite, trace(X) = t,
and optionally one more equality <A, X> = b. Input: C = [c11, c12, c22] and, when given,
A = [a11, a12, a22], integers -20..20; trace t an integer 1..50; b an integer -1000..1000.

Writing u = t/2, v = (x - z)/2 the trace equality gives x = u + v, z = u - v, and X is
positive semidefinite exactly when v^2 + y^2 <= u^2 (a disk). The objective is linear in
(v, y) and the optional equality is a line r*v + s*y = g, so the optimum is found in
closed form: the point of the disk facing -(p, q) without the extra equality, or an
endpoint of the chord cut by the line. Every value is an exact element of Q(sqrt(m)), m a
squarefree integer; no rounding occurs. The result carries its own exact checks (trace,
extra equality, x >= 0, z >= 0, det >= 0 and the objective recomputed from the optimizer),
and without the extra equality an exact dual certificate: the multiplier w for the trace
equality gives S = C - w*I positive semidefinite with <S, X> = 0, so the primal value
equals t*w.

Scope: PARTIAL for the Semidefinite Programming line. It is a real SDP over 2x2 matrices
with one or two affine equalities, solved exactly. It is not a general-size solver: no
n >= 3 matrices, no inequality constraints, no interior-point iteration. With the extra
equality it reports no dual certificate; optimality there rests on the chord geometry.

Not claimed: that the program models any real problem, that a solver of larger matrices
would agree, that an unreported dual certificate exists, or anything about the real
world. Every claim flag in the result is False.
"""
from fractions import Fraction

MAX_ENTRY = 20
MAX_TRACE = 50
MAX_B = 1000
_TOP = frozenset({"C", "trace", "constraint"})
_CON = frozenset({"A", "b"})

NOT_CLAIMED = (
    "the program models a real problem",
    "a solver of larger matrices would agree",
    "an unreported dual certificate exists",
    "real-world outcome",
)
CLAIMS = {"models_real_problem": False, "larger_matrices": False, "unreported_certificate": False, "real_world": False}


class SdpError(ValueError):
    pass


def _int(v, lo, hi, name):
    if isinstance(v, bool) or not isinstance(v, int):
        raise SdpError(f"{name} must be an int")
    if v < lo or v > hi:
        raise SdpError(f"{name} out of range")
    return v


def _sym(v, name):
    if not isinstance(v, list) or len(v) != 3:
        raise SdpError(f"{name} must be a list of 3 ints")
    return [_int(q, -MAX_ENTRY, MAX_ENTRY, f"{name} entry") for q in v]


def _squarefree(q):
    """q > 0 Fraction -> (k, m) with sqrt(q) = k*sqrt(m), m a squarefree integer."""
    n = q.numerator * q.denominator  # sqrt(q) = sqrt(n) / den
    k, m, p = 1, 1, 2
    while p * p <= n:
        while n % (p * p) == 0:
            n //= p * p
            k *= p
        if n % p == 0:
            n //= p
            m *= p
        p += 1
    m *= n
    return Fraction(k, q.denominator), m


class _S:
    """a + b*sqrt(m) with exact Fractions; m is shared by one computation."""
    __slots__ = ("a", "b", "m")

    def __init__(self, a, b, m):
        self.a, self.b, self.m = Fraction(a), Fraction(b), m

    def __add__(self, o):
        o = self._c(o)
        return _S(self.a + o.a, self.b + o.b, self.m)

    __radd__ = __add__

    def __sub__(self, o):
        o = self._c(o)
        return _S(self.a - o.a, self.b - o.b, self.m)

    def __rsub__(self, o):
        return self._c(o) - self

    def __mul__(self, o):
        o = self._c(o)
        return _S(self.a * o.a + self.b * o.b * self.m, self.a * o.b + self.b * o.a, self.m)

    __rmul__ = __mul__

    def _c(self, o):
        return o if isinstance(o, _S) else _S(o, 0, self.m)

    def sign(self):
        a, b = self.a, self.b
        if self.m == 1:
            a, b = a + b, Fraction(0)
        if b == 0:
            return (a > 0) - (a < 0)
        if a == 0:
            return (b > 0) - (b < 0)
        if a > 0 and b > 0:
            return 1
        if a < 0 and b < 0:
            return -1
        sq = a * a - b * b * self.m  # sign of a + b sqrt(m) is the sign of the larger-magnitude part
        if a > 0:  # b < 0
            return 1 if sq > 0 else (-1 if sq < 0 else 0)
        return -1 if sq > 0 else (1 if sq < 0 else 0)  # a < 0, b > 0

    def key(self):
        if self.m == 1 or self.b == 0:
            return [str(self.a + (self.b if self.m == 1 else 0)), "0"]
        return [str(self.a), str(self.b)]


def semidefinite_programming(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise SdpError("data keys must be exactly C, trace, constraint")
    C = _sym(data["C"], "C")
    t = _int(data["trace"], 1, MAX_TRACE, "trace")
    con = data["constraint"]
    if con is not None:
        if not isinstance(con, dict) or set(con) != _CON:
            raise SdpError("constraint must be None or have keys exactly A, b")
        A = _sym(con["A"], "A")
        bval = _int(con["b"], -MAX_B, MAX_B, "b")
    u = Fraction(t, 2)
    const = Fraction((C[0] + C[2]) * t, 2)
    p, q = Fraction(C[0] - C[2]), Fraction(2 * C[1])

    if con is not None:
        r, s = Fraction(A[0] - A[2]), Fraction(2 * A[1])
        g = bval - Fraction(A[0] + A[2]) * u
        if r == 0 and s == 0:
            if g != 0:
                raise SdpError("constraint is infeasible")
            con = None
    pq = p * p + q * q
    if con is None:
        if pq == 0:
            m, v, y = 1, _S(0, 0, 1), _S(0, 0, 1)
            val = _S(const, 0, 1)
            unique = False
            w = _S(const / t, 0, 1)
        else:
            k, m = _squarefree(pq)
            # sqrt(pq) = k*sqrt(m), so v = -u*p/sqrt(pq) = -u*p*sqrt(m)/(k*m)
            v = _S(0, -(u * p) / (k * m), m)
            y = _S(0, -(u * q) / (k * m), m)
            val = _S(const, -u * k, m)
            unique = True
            w = _S(const / t, -(u * k) / t, m)
        cert_flag = True
    else:
        N2 = r * r + s * s
        R = u * u * N2 - g * g
        if R < 0:
            raise SdpError("constraint is infeasible")
        cert_flag = False
        foot_v, foot_y = g * r / N2, g * s / N2
        if R == 0:
            m, v, y = 1, _S(foot_v, 0, 1), _S(foot_y, 0, 1)
            val = _S(const + p * foot_v + q * foot_y, 0, 1)
            unique = True
        else:
            k, m = _squarefree(R)  # sqrt(R) = k*sqrt(m); w = sqrt(R)
            cross = q * r - p * s
            sg = (cross > 0) - (cross < 0)
            # chord points: foot + tau*(w/N2)*(-s, r); objective change tau*(w/N2)*cross, take tau = -sign(cross)
            tau = -sg if sg else -1
            coef = tau * k / N2
            v = _S(foot_v, coef * (-s), m)
            y = _S(foot_y, coef * r, m)
            val = _S(const + p * foot_v + q * foot_y, tau * k * cross / N2, m)
            unique = sg != 0
    uu = _S(u, 0, m)
    x = uu + v
    z = uu - v
    # exact checks, recomputed from the optimizer
    obj = C[0] * x + 2 * C[1] * y + C[2] * z
    trace_ok = (x + z - t).sign() == 0
    extra_ok = True
    if data["constraint"] is not None:
        extra_ok = (A[0] * x + 2 * A[1] * y + A[2] * z - bval).sign() == 0
    psd_ok = x.sign() >= 0 and z.sign() >= 0 and (x * z - y * y).sign() >= 0
    value_ok = (obj - val).sign() == 0
    out = {
        "status": "optimal",
        "radicand": m,
        "optimal_value": val.key(),
        "optimizer": {"x": x.key(), "y": y.key(), "z": z.key()},
        "optimizer_unique": unique,
        "trace_ok": trace_ok,
        "constraint_ok": extra_ok,
        "psd_ok": psd_ok,
        "value_ok": value_ok,
        "dual_certificate": None,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
    if cert_flag:
        # S = C - w*I; psd: s11 >= 0, s22 >= 0, det >= 0; complementarity <S, X> = 0; primal value = t*w
        s11, s22 = C[0] - w, C[2] - w
        s12 = _S(C[1], 0, m)
        comp = s11 * x + 2 * s12 * y + s22 * z
        out["dual_certificate"] = {
            "multiplier": w.key(),
            "slack_psd": s11.sign() >= 0 and s22.sign() >= 0 and (s11 * s22 - s12 * s12).sign() >= 0,
            "complementarity_zero": comp.sign() == 0,
            "dual_value_equals_primal": (t * w - val).sign() == 0,
        }
    return out
