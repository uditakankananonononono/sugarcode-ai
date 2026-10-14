"""Row 258, Game-Theoretic Learning: two-sided regret matching on a zero-sum game.

Finite two-player zero-sum matrix game; A[i][j] in [0, 1] is the payoff to the row
player (the column player gets the negative). In each round both players use
regret matching against the other's actual current mixed policy (full
information): row payoff vector u_i = sum_j A[i][j] y_j, column payoff vector
v_j = -sum_i x_i A[i][j]. Reported: the average strategies xbar and ybar and the
exact exploitability certificate
  gap = max_i (A ybar)_i - min_j (xbar A)_j  >= 0,
which brackets the game value: min_j (xbar A)_j <= value <= max_i (A ybar)_i.
gap = 0 exactly means (xbar, ybar) is a Nash equilibrium of the game.
Caps: 1 to 4 rows and columns, 1 to 8 rounds (exact fractions grow quickly),
entries nonbool int or Fraction with numerator and denominator at most 32 bits,
in [0, 1]. Checks run before any scan.

NOT_CLAIMED: zero-sum two-player case only, not a general-sum claim. No
convergence rate or guarantee that gap is small after the given rounds; the
certificate is exact for the returned strategies whatever the round count. Payoffs
are caller inputs, not verified; no real-world, clinical or wet-lab claim.
"""
from fractions import Fraction

MAX_K, MAX_ROUNDS = 4, 8


def _q(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def _policy(R, k):
    pos = [max(r, 0) for r in R]
    s = sum(pos)
    return [Fraction(1, k)] * k if s == 0 else [v / s for v in pos]


def learn_zero_sum(A, rounds):
    if type(rounds) is not int:
        raise TypeError('rounds must be a nonbool int')
    if not 1 <= rounds <= MAX_ROUNDS:
        raise ValueError('rounds must be between 1 and 8')
    if type(A) not in (list, tuple) or not 1 <= len(A) <= MAX_K:
        raise ValueError('A must have 1 to 4 rows')
    for row in A:
        if type(row) not in (list, tuple):
            raise TypeError('A must be a list or tuple of rows')
    m = len(A)
    n = len(A[0])
    if not 1 <= n <= MAX_K:
        raise ValueError('A must have 1 to 4 columns')
    if any(len(row) != n for row in A):
        raise ValueError('A rows must have equal length')
    M = [[_q(v) for v in row] for row in A]
    if any(v < 0 or v > 1 for row in M for v in row):
        raise ValueError('entries must be in [0, 1]')
    Rx, Ry = [Fraction(0)] * m, [Fraction(0)] * n
    sx, sy = [Fraction(0)] * m, [Fraction(0)] * n
    for _ in range(rounds):
        x, y = _policy(Rx, m), _policy(Ry, n)
        sx = [sx[i] + x[i] for i in range(m)]
        sy = [sy[j] + y[j] for j in range(n)]
        u = [sum(M[i][j] * y[j] for j in range(n)) for i in range(m)]
        v = [-sum(x[i] * M[i][j] for i in range(m)) for j in range(n)]
        gu, gv = sum(x[i] * u[i] for i in range(m)), sum(y[j] * v[j] for j in range(n))
        Rx = [Rx[i] + u[i] - gu for i in range(m)]
        Ry = [Ry[j] + v[j] - gv for j in range(n)]
    xb = [t / rounds for t in sx]
    yb = [t / rounds for t in sy]
    upper = max(sum(M[i][j] * yb[j] for j in range(n)) for i in range(m))
    lower = min(sum(xb[i] * M[i][j] for i in range(m)) for j in range(n))
    return {'row_average': xb, 'column_average': yb, 'value_lower': lower,
            'value_upper': upper, 'exploitability': upper - lower,
            'is_equilibrium': upper == lower}
