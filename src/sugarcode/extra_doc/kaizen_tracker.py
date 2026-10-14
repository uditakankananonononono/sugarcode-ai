"""Row 462, Continuous Improvement: exact trend of a measure over improvement periods, and cycles to a target.

improvement_trend(values) takes one measurement per period (a defect rate, minutes per job, ... where lower is
better; periods are 0, 1, 2, ... equally spaced) and returns, exactly: slope and intercept of the least-squares line
(Fractions), steps_improving (how many period-to-period steps went strictly down), longest_improving_streak (most
consecutive strictly improving steps), total_change (last - first), relative_reduction ((first - last) / first, None
when first is 0) and improving (slope < 0).
cycles_to_target(current, target, reduction) answers: if every improvement cycle cuts the measure by the fraction
reduction (it is multiplied by 1 - reduction), how many cycles are needed before it is at most target? Returns cycles (the
smallest n with current * (1 - reduction) ** n <= target, found by exact integer comparison), the value after those
cycles and reachable. When more than 200 cycles would be needed (or target is 0 with current above 0) it returns
cycles None and reachable False.
Caps: 2 to 60 values; values, current and target nonbool int or Fraction with 32-bit numerator and denominator in
[0, 1000000]; reduction in (0, 1) the same way; current above target is not required (zero cycles if already at or
below). Order of checks: types, widths and ranges in argument order (values in order), and only then any computation.

NOT_CLAIMED: arithmetic only. It does not say that a change was caused by any improvement activity, that a trend
will continue, that the measure is the right one, or that a kaizen culture exists; a constant percentage cut per
cycle is an assumption, not a forecast. No clinical or wet-lab claim.
"""
from fractions import Fraction

LIM = 1000000
MAX_CYCLES = 200


def _num(v, what):
    if type(v) not in (int, Fraction):
        raise TypeError(what + ' must be a nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    if not 0 <= f <= LIM:
        raise ValueError(what + ' must be between 0 and 1000000')
    return f


def improvement_trend(values):
    if type(values) not in (list, tuple):
        raise TypeError('values must be a list or tuple')
    if not 2 <= len(values) <= 60:
        raise ValueError('value count must be between 2 and 60')
    ys = [_num(v, 'value') for v in values]
    n = len(ys)
    sx = Fraction(n * (n - 1), 2)
    sxx = Fraction((n - 1) * n * (2 * n - 1), 6)
    sy = sum(ys)
    sxy = sum(i * y for i, y in enumerate(ys))
    slope = (n * sxy - sx * sy) / (n * sxx - sx * sx)
    intercept = (sy - slope * sx) / n
    streak = best = steps = 0
    for a, b in zip(ys, ys[1:]):
        if b < a:
            steps += 1
            streak += 1
            best = max(best, streak)
        else:
            streak = 0
    first, last = ys[0], ys[-1]
    return {'slope': slope, 'intercept': intercept, 'steps_improving': steps, 'longest_improving_streak': best,
            'total_change': last - first, 'relative_reduction': None if first == 0 else (first - last) / first,
            'improving': slope < 0}


def cycles_to_target(current, target, reduction):
    cur = _num(current, 'current')
    tgt = _num(target, 'target')
    r = Fraction(reduction) if type(reduction) in (int, Fraction) else None
    if r is None:
        raise TypeError('reduction must be a nonbool int or Fraction')
    if r.numerator.bit_length() > 32 or r.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    if not 0 < r < 1:
        raise ValueError('reduction must be between 0 and 1, exclusive')
    keep = 1 - r
    val = cur
    for n in range(MAX_CYCLES + 1):
        if val <= tgt:
            return {'cycles': n, 'value_after': val, 'reachable': True}
        val = val * keep
    return {'cycles': None, 'value_after': None, 'reachable': False}
