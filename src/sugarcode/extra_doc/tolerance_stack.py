"""Row 330, Industrial Design: exact tolerance stack-up for a manufactured assembly.

An assembly gap is a signed sum of part dimensions. Each item is (nominal, plus, minus, sign):
the part is made between nominal - minus and nominal + plus, and it adds to the gap (sign +1) or
takes from it (sign -1). stack_up(items, gap_min, gap_max) returns, as exact Fractions:
- nominal_gap = sum(sign * nominal);
- worst_low and worst_high: the smallest and largest gap over every in-tolerance combination
  (worst-case method); worst_case_ok when gap_min <= worst_low and worst_high <= gap_max;
- mean_gap: the gap when every part sits at the middle of its band, mean_gap = sum(sign * (nominal +
  (plus - minus) / 2));
- spread_squared: sum(((plus + minus) / 2) ** 2), the quantity under the root of the root-sum-square
  (RSS) method. rss_ok is the exact test that the mean gap stays inside the limits by at least
  the RSS spread: mean_gap - gap_min >= 0, gap_max - mean_gap >= 0 and each squared margin is at least
  spread_squared. No square root is taken, so the answer is exact;
- shares: each item's fraction of the total worst-case band (worst_high - worst_low) as a Fraction, or 0
  everywhere when the band is zero.
Caps: 1 to 12 items; nominal 0 to 10000 and plus and minus 0 to 1000 as nonbool int or Fraction with 32-bit
numerator and denominator; sign exactly 1 or -1 (nonbool int); gap limits -100000 to 100000, gap_min <= gap_max.
Order of checks: item list, then each item in order (structure, types, ranges), then the two limits, and only
then any computation.

NOT_CLAIMED: this is the arithmetic of two textbook stack-up methods only. RSS assumes independent, centred,
roughly normal part errors and says nothing about real process capability; no GD&T, thermal or wear effects, no
manufacturability, cost, safety, standards compliance or product quality judgement. No clinical or wet-lab claim.
"""
from fractions import Fraction

MAX_ITEMS = 12


def _num(v, what):
    if type(v) not in (int, Fraction):
        raise TypeError(what + ' must be a nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def stack_up(items, gap_min, gap_max):
    if type(items) not in (list, tuple):
        raise TypeError('items must be a list or tuple')
    if not 1 <= len(items) <= MAX_ITEMS:
        raise ValueError('item count must be between 1 and 12')
    clean = []
    for it in items:
        if type(it) not in (list, tuple) or len(it) != 4:
            raise TypeError('each item must be (nominal, plus, minus, sign)')
        nom = _num(it[0], 'nominal')
        plus = _num(it[1], 'plus')
        minus = _num(it[2], 'minus')
        if type(it[3]) is not int:
            raise TypeError('sign must be a nonbool int')
        if not 0 <= nom <= 10000:
            raise ValueError('nominal must be between 0 and 10000')
        if not 0 <= plus <= 1000 or not 0 <= minus <= 1000:
            raise ValueError('plus and minus must be between 0 and 1000')
        if it[3] not in (1, -1):
            raise ValueError('sign must be 1 or -1')
        clean.append((nom, plus, minus, it[3]))
    lo, hi = _num(gap_min, 'gap_min'), _num(gap_max, 'gap_max')
    if not -100000 <= lo <= 100000 or not -100000 <= hi <= 100000:
        raise ValueError('gap limits must be between -100000 and 100000')
    if lo > hi:
        raise ValueError('gap_min must not exceed gap_max')
    nominal = sum(s * n for n, p, m, s in clean)
    low = high = Fraction(0)
    bands = []
    for n, p, m, s in clean:
        if s > 0:
            low += n - m
            high += n + p
        else:
            low -= n + p
            high -= n - m
        bands.append(p + m)
    mean = sum(s * (n + (p - m) / 2) for n, p, m, s in clean)
    spread2 = sum(((p + m) / 2) ** 2 for n, p, m, s in clean)
    total = high - low
    rss_ok = (mean - lo >= 0 and hi - mean >= 0 and (mean - lo) ** 2 >= spread2 and (hi - mean) ** 2 >= spread2)
    return {'nominal_gap': Fraction(nominal), 'worst_low': low, 'worst_high': high,
            'worst_case_ok': lo <= low and high <= hi, 'mean_gap': Fraction(mean),
            'spread_squared': Fraction(spread2), 'rss_ok': rss_ok,
            'shares': [b / total if total else Fraction(0) for b in bands]}
