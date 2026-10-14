"""Row 501: Valuation Analysis - Estimates worth.

PARTIAL: multiplies a supplied metric by supplied integer multiples,
reporting scenario values, smallest/largest value and spread.
No fair-value assessment, market evidence or investment advice.
Caps of 1-12 multiples in 1-100 and metric 0-1000000 are this module's choices.
"""
MAX_MULTIPLES = 12
MAX_MULTIPLE = 100
MAX_METRIC = 1000000
NOT_CLAIMED = ('fair_value', 'market_evidence', 'investment_advice')


def values(metric, multiples):
    if type(multiples) is not tuple or not 1 <= len(multiples) <= MAX_MULTIPLES:
        raise ValueError('multiples: tuple of 1 to 12 entries required')
    if type(metric) is not int or not 0 <= metric <= MAX_METRIC:
        raise ValueError('metric: whole number 0 to 1000000 required')
    for i,value in enumerate(multiples):
        if type(value) is not int or not 1 <= value <= MAX_MULTIPLE:
            raise ValueError(f'multiples[{i}]: whole number 1 to 100 required')
    scenarios = tuple(metric * multiple for multiple in multiples)
    low = scenarios[min(range(len(scenarios)), key=lambda i: scenarios[i])]
    high = scenarios[max(range(len(scenarios)), key=lambda i: scenarios[i])]
    return {'valuation_multiple_validated': False, 'not_claimed': NOT_CLAIMED,
            'scenarios': scenarios, 'low': low, 'high': high, 'spread': high - low}
