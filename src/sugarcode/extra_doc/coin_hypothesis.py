"""Row 861, Scientific Thinking - Tests hypotheses: exact fair-coin test.

coin_hypothesis takes name, a printable ASCII string of 1 to 12 characters
naming the hypothesis (control characters are refused), trials, a nonbool int
from 1 to 30, heads, a nonbool int from 0 to trials, and alpha, a nonbool int
from 1 to 50 (default 5, a percent).
The hypothesis is that the coin is fair. Every outcome of the trials flips is
counted by number of heads, and an outcome set is as extreme as the observed
one when its count of sequences is no larger than the observed count.
Returns name, tail_count (the sequences in all head counts that are as extreme
as the observed one), total (2 to the power trials), p_permille (tail_count
over total, in thousandths, rounded down) and reject (True when tail_count is
below alpha percent of total, compared exactly).
Checks, in this order: name, trials, heads, alpha.
NOT_CLAIMED: real scientific thinking, experiment design, effect size,
multiple testing, production readiness.
"""
from math import comb

SCOPE = 'PARTIAL: exact two-sided fair-coin tail count for supplied flips, no science is done'
NOT_CLAIMED = ('real scientific thinking', 'experiment design', 'effect size',
               'multiple testing', 'production readiness')


def coin_hypothesis(name, trials, heads, alpha=5):
    if type(name) is not str or not name.isascii() or not name.isprintable() or not 1 <= len(name) <= 12:
        raise ValueError('name must be a printable ASCII string of 1 to 12 characters')
    if type(trials) is not int or not 1 <= trials <= 30:
        raise ValueError('trials must be a nonbool integer between 1 and 30')
    if type(heads) is not int or not 0 <= heads <= trials:
        raise ValueError('heads must be a nonbool integer between 0 and trials')
    if type(alpha) is not int or not 1 <= alpha <= 50:
        raise ValueError('alpha must be a nonbool integer between 1 and 50')
    seen = comb(trials, heads)
    tail = sum(c for c in (comb(trials, i) for i in range(trials + 1)) if c <= seen)
    total = 2 ** trials
    return {'name': name, 'tail_count': tail, 'total': total,
            'p_permille': tail * 1000 // total, 'reject': tail * 100 < alpha * total}
