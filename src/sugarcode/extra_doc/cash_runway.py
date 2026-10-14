"""Row 500: Financial Modeling - Projects financials.

PARTIAL: replays supplied period revenue/expense counts against a starting
cash count, returning closing balances and first negative position.
No financial prediction, business model or accounting validation.
Caps of 1-24 periods and counts 0-1000000 are this module's choices.
"""
MAX_PERIODS = 24
MAX_AMOUNT = 1000000
NOT_CLAIMED = ('financial_prediction', 'business_model', 'accounting_validation')


def runway(periods, starting_cash):
    if type(periods) is not tuple or not 1 <= len(periods) <= MAX_PERIODS:
        raise ValueError('periods: tuple of 1 to 24 pairs required')
    if type(starting_cash) is not int or not 0 <= starting_cash <= MAX_AMOUNT:
        raise ValueError('starting_cash: whole number 0 to 1000000 required')
    for i,row in enumerate(periods):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'periods[{i}]: pair (revenue, expense) required')
        for name,value in zip(('revenue','expense'),row):
            if type(value) is not int or not 0 <= value <= MAX_AMOUNT:
                raise ValueError(f'periods[{i}].{name}: whole number 0 to 1000000 required')
    balance = starting_cash
    closing = []
    for revenue,expense in periods:
        balance += revenue - expense
        closing.append(balance)
    negative = tuple(i for i in range(len(closing)) if closing[i] < 0)
    return {'cash_runway_validated': False, 'not_claimed': NOT_CLAIMED,
            'closing_balances': tuple(closing), 'final_cash': balance,
            'first_negative': negative[0] if negative else None,
            'nonnegative_throughout': not negative}
