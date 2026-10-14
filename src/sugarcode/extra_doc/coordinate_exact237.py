"""Exact rational cyclic coordinate descent for supplied SPD quadratics.
NOT_CLAIMED: arbitrary objective; finite-budget exact global optimum; authentic
model; real-world execution; distributed system; runtime integration.
"""
from fractions import Fraction
import math

def solve(matrix, linear, initial, sweeps, tolerance):
    if type(sweeps) is not int or not 1 <= sweeps <= 30:
        raise ValueError('strict coordinate sweeps 1..30')
    if type(initial) is not list or not 1 <= len(initial) <= 8:
        raise ValueError('1..8 coordinate dimensions before scan')
    n = len(initial)

    def number(v, lo, hi):
        if type(v) not in (int, float) or not lo <= v <= hi or (not math.isfinite(v)):
            raise ValueError('strict finite bounded coordinate number')
        return Fraction(str(v))

    def vector(v):
        if type(v) is not list or len(v) != n:
            raise ValueError('one value per coordinate dimension')
        return [number(q, -1000, 1000) for q in v]
    x = vector(initial)
    b = vector(linear)
    tol = number(tolerance, 1e-09, 1)
    if type(matrix) is not list or len(matrix) != n:
        raise ValueError('square coordinate matrix dimension')
    a = [vector(row) for row in matrix]
    if any((a[i][j] != a[j][i] for i in range(n) for j in range(n))):
        raise ValueError('symmetric coordinate matrix')
    lower = [{} for _ in range(n)]
    pivots = []
    for i in range(n):
        p = a[i][i] - sum((lower[i][k] ** 2 * pivots[k] for k in range(i)))
        if p < Fraction(1, 1000000):
            raise ValueError('positive definite coordinate matrix pivots >=1e-6')
        pivots.append(p)
        for j in range(i + 1, n):
            lower[j][i] = (a[j][i] - sum((lower[j][k] * lower[i][k] * pivots[k] for k in range(i)))) / p

    def objective():
        return sum((a[i][j] * x[i] * x[j] / 2 for i in range(n) for j in range(n))) - sum((q * v for q, v in zip(b, x)))

    def gradient():
        return [sum((q * v for q, v in zip(row, x))) - c for row, c in zip(a, b)]
    trace = []
    history = [str(objective())]
    converged = False
    for sweep in range(1, sweeps + 1):
        for j in range(n):
            before = x[:]
            old = x[j]
            x[j] = (b[j] - sum((a[j][k] * x[k] for k in range(n) if k != j))) / a[j][j]
            trace.append({'sweep': sweep, 'coordinate': j, 'old_fraction': str(old), 'point_before_fraction': [str(q) for q in before], 'point_after_fraction': [str(q) for q in x], 'objective_fraction': str(objective())})
            history.append(str(objective()))
        used = sweep
        if max((abs(q) for q in gradient())) <= tol:
            converged = True
            break
    g = gradient()
    return {'point_fraction': [str(q) for q in x], 'objective_fraction': str(objective()), 'objective_history_fraction': history, 'trace': trace, 'gradient_fraction': [str(q) for q in g], 'gradient_infinity_fraction': str(max((abs(q) for q in g))), 'converged_gradient_tolerance': converged, 'sweeps_used': used, 'method': 'exact cyclic one-coordinate quadratic minimization', 'objective_definition': '0.5*x^T*A*x - b^T*x', 'global_optimum_claimed': False, 'external_effects': []}
