"""Row 461, Total Quality Management: exact control-chart signals and process-capability test.

control_chart_signals(points, center, sigma) applies four Western Electric zone rules to a run of
measurements, using exact z = (x - center) / sigma (Fractions, no rounding). For each rule it lists the
0-based indices where the rule fires:
- rule1: one point beyond 3 sigma (|z| > 3);
- rule2: at point i, at least 2 of the 3 points ending at i are beyond 2 sigma on the same side as point i
  itself (z_i > 2, or z_i < -2, and the window holds at least two such points on that side);
- rule3: at least 4 of the 5 points ending at i are beyond 1 sigma on the same side as point i itself;
- rule4: the 8 points ending at i all lie strictly on the same side of the centre line.
A point exactly on a boundary does not count as beyond it. in_control is True when no rule fires.
capability(samples, lsl, usl, target) takes measurements and the specification limits, and returns the mean and
sample variance (divisor n - 1) as Fractions, cp_squared = ((usl - lsl) / 6) ** 2 / variance, cpk_margin =
min(usl - mean, mean - lsl) and cpk_squared = cpk_margin ** 2 / (9 * variance) (None when the variance is 0), and
two exact tests against target (for example 4/3): cp_ok when Cp >= target (cp_squared >= target ** 2) and cpk_ok when
cpk_margin >= 0 and Cpk >= target. With zero variance Cp is infinite, so cp_ok is True and cpk_ok is cpk_margin > 0.
No square roots are taken, so every verdict is exact.
Caps: 1 to 100 values, each a nonbool int or Fraction with 32-bit numerator and denominator in [-1000000, 1000000];
sigma in (0, 1000000]; at least 2 samples for capability; lsl < usl; target in (0, 10]. Order of checks: the list and its
length, then each value in order (type, width, range), then the other arguments in argument order, and only then any
computation.

NOT_CLAIMED: arithmetic on supplied numbers only. It does not check that data are independent or normal, that
sigma was estimated from a stable process, that the specification is the right one, or that a quality culture
exists; the four rules are the classic textbook set, not a complete monitoring scheme. No clinical or wet-lab claim.
"""
from fractions import Fraction

LIM = 1000000


def _num(v, what):
    if type(v) not in (int, Fraction):
        raise TypeError(what + ' must be a nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def _series(vals, what):
    if type(vals) not in (list, tuple):
        raise TypeError(what + ' must be a list or tuple')
    if not 1 <= len(vals) <= 100:
        raise ValueError(what + ' count must be between 1 and 100')
    out = []
    for v in vals:
        f = _num(v, what[:-1] + ' value')
        if not -LIM <= f <= LIM:
            raise ValueError(what[:-1] + ' value must be between -1000000 and 1000000')
        out.append(f)
    return out


def control_chart_signals(points, center, sigma):
    xs = _series(points, 'points')
    c = _num(center, 'center')
    if not -LIM <= c <= LIM:
        raise ValueError('center must be between -1000000 and 1000000')
    s = _num(sigma, 'sigma')
    if not 0 < s <= LIM:
        raise ValueError('sigma must be greater than 0 and at most 1000000')
    z = [(x - c) / s for x in xs]
    r1, r2, r3, r4 = [], [], [], []
    for i, zi in enumerate(z):
        if abs(zi) > 3:
            r1.append(i)
        for sign in (1, -1):
            if sign * zi > 2 and sum(1 for v in z[max(0, i - 2):i + 1] if sign * v > 2) >= 2:
                r2.append(i)
            if sign * zi > 1 and sum(1 for v in z[max(0, i - 4):i + 1] if sign * v > 1) >= 4:
                r3.append(i)
        if i >= 7 and (all(v > 0 for v in z[i - 7:i + 1]) or all(v < 0 for v in z[i - 7:i + 1])):
            r4.append(i)
    return {'rule1': r1, 'rule2': r2, 'rule3': r3, 'rule4': r4, 'in_control': not (r1 or r2 or r3 or r4),
            'z': z}


def capability(samples, lsl, usl, target):
    xs = _series(samples, 'samples')
    if len(xs) < 2:
        raise ValueError('at least 2 samples are needed')
    lo = _num(lsl, 'lsl')
    hi = _num(usl, 'usl')
    if not -LIM <= lo <= LIM or not -LIM <= hi <= LIM:
        raise ValueError('specification limits must be between -1000000 and 1000000')
    if not lo < hi:
        raise ValueError('lsl must be below usl')
    t = _num(target, 'target')
    if not 0 < t <= 10:
        raise ValueError('target must be greater than 0 and at most 10')
    n = len(xs)
    mean = sum(xs) / n
    var = sum((x - mean) ** 2 for x in xs) / (n - 1)
    margin = min(hi - mean, mean - lo)
    if var == 0:
        return {'mean': mean, 'variance': var, 'cp_squared': None, 'cpk_margin': margin, 'cpk_squared': None,
                'cp_ok': True, 'cpk_ok': margin > 0}
    cp2 = ((hi - lo) / 6) ** 2 / var
    cpk2 = margin ** 2 / (9 * var)
    return {'mean': mean, 'variance': var, 'cp_squared': cp2, 'cpk_margin': margin, 'cpk_squared': cpk2,
            'cp_ok': cp2 >= t * t, 'cpk_ok': margin >= 0 and cpk2 >= t * t}
