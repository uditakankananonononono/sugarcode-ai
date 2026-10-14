"""Row 375 Product-Market Fit Assessment - Measures market validation: supplied survey tally.

Responses are strings from very_disappointed, somewhat_disappointed,
not_disappointed (the answers to "how would you feel if you could no longer use
the product"). Returns counts, the exact share of very_disappointed answers, and
whether that share is at least 2/5. 1 to 200 responses. The 2/5 line is a
commonly quoted rule of thumb, an implementation choice here, not a spec value.
NOT_CLAIMED: that product-market fit exists, sample representativeness or size
adequacy, honesty of responses, retention, revenue, causal claims or demand.
"""
from fractions import Fraction

ANSWERS = ('very_disappointed', 'somewhat_disappointed', 'not_disappointed')


def assess_fit(responses):
    if type(responses) not in (list, tuple):
        raise TypeError('responses must be a list or tuple')
    if not 1 <= len(responses) <= 200:
        raise ValueError('response count must be between 1 and 200')
    if any(type(r) is not str or r not in ANSWERS for r in responses):
        raise ValueError('responses must be very_disappointed, somewhat_disappointed or not_disappointed')
    counts = {a: sum(1 for r in responses if r == a) for a in ANSWERS}
    share = Fraction(counts['very_disappointed'], len(responses))
    return {'counts': counts, 'total': len(responses), 'very_disappointed_share': share,
            'meets_two_fifths': share >= Fraction(2, 5), 'fit_validated': False}
