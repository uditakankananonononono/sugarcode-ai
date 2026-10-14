"""Row 251: Online Learning - Adapts to streaming data.

Exact projected online gradient descent on a bounded box for a supplied
stream of linear loss gradients. Predict before seeing each loss, then
update. Returns actual regret against the best fixed box comparator and
the standard constant-step Euclidean regret bound.
NOT_CLAIMED: nonlinear loss or gradient acquisition, unbounded domains,
adaptive step schedules, statistical generalization, biological validation.
"""
from fractions import Fraction


def _scalar(v):
    if type(v) not in (int, Fraction):
        raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length() > 32:
            raise ValueError('rational values must fit 32 bits')
    elif v.numerator.bit_length() > 32 or v.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return Fraction(v)


def projected_online_gradient(gradients, lower, upper, initial, step_size=1):
    if any(type(v) not in (list, tuple) for v in (gradients, lower, upper, initial)):
        raise TypeError('inputs must be lists or tuples')
    n = len(lower)
    if not 1 <= n <= 8:
        raise ValueError('dimension count must be between 1 and 8')
    if not 1 <= len(gradients) <= 256:
        raise ValueError('round count must be between 1 and 256')
    if len(upper) != n or len(initial) != n:
        raise ValueError('vector dimensions must agree')
    if any(type(row) not in (list, tuple) or len(row) != n for row in gradients):
        raise ValueError('gradient dimensions must agree')
    lo = [_scalar(v) for v in lower]
    hi = [_scalar(v) for v in upper]
    x = [_scalar(v) for v in initial]
    gs = [[_scalar(v) for v in row] for row in gradients]
    eta = _scalar(step_size)
    if eta <= 0:
        raise ValueError('step_size must be positive')
    if any(a > b for a, b in zip(lo, hi)):
        raise ValueError('lower bounds must not exceed upper bounds')
    if any(not a <= v <= b for a, v, b in zip(lo, x, hi)):
        raise ValueError('initial point must be inside box')
    trace = []
    learner_loss = Fraction(0)
    for t, g in enumerate(gs, 1):
        prediction = x[:]
        loss = sum((a * b for a, b in zip(g, prediction)), Fraction(0))
        learner_loss += loss
        x = [min(b, max(a, v - eta * h)) for a, b, v, h in zip(lo, hi, x, g)]
        trace.append({'round': t, 'prediction': prediction, 'loss': loss, 'next_point': x[:]})
    totals = [sum((g[i] for g in gs), Fraction(0)) for i in range(n)]
    comparator = [a if total >= 0 else b for a, b, total in zip(lo, hi, totals)]
    comparator_loss = sum((a * b for a, b in zip(totals, comparator)), Fraction(0))
    regret = learner_loss - comparator_loss
    diameter_squared = sum(((b - a)**2 for a, b in zip(lo, hi)), Fraction(0))
    gradient_energy = sum((v*v for row in gs for v in row), Fraction(0))
    bound = diameter_squared / (2 * eta) + eta * gradient_energy / 2
    return {'final_point': x, 'trace': trace, 'learner_loss': learner_loss,
            'comparator': comparator, 'comparator_loss': comparator_loss,
            'regret': regret, 'regret_bound': bound, 'certificate_valid': regret <= bound}
