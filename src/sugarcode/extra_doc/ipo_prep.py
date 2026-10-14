"""Row 509 IPO Preparation: exact checklist progress and offering dilution arithmetic.

checklist_progress: the caller supplies 1 to 20 unique items (name, weight, status): weight an int 1 to
10, status 0 not started, 1 in progress or 2 done, and a blocker cutoff (int 1 to 10). Reported: the
weighted done share and in-progress share (Fractions of total weight) and the items not done whose
weight is at or above the cutoff, in input order.
offering_math: pre-offering shares (int 1 to 10**10), new shares offered (int 0 to 10**10) and offer
price (int 1 to 10**9). Reported: gross proceeds, pre-money and post-money value (Fractions or ints at
the offer price), the share of the enlarged company kept by existing holders and held by new
investors. Fees, over-allotment, lock-ups and taxes are left out. Caps are implementation choices,
not spec values. No filing, regulation or market data is used.
NOT_CLAIMED: that the checklist items are the required ones or complete, that a status is accurate,
that a company is ready or eligible to list, the price, valuation or demand, securities, listing or
disclosure law, advice of any kind, approval-gate clearance, deployment.
"""
from fractions import Fraction

NOT_CLAIMED = ('checklist items the required ones or complete', 'a status accurate',
               'a company ready or eligible to list', 'price, valuation or demand',
               'securities, listing or disclosure law', 'advice of any kind', 'approval-gate clearance',
               'deployment')


def checklist_progress(items, cutoff):
    if type(cutoff) is not int:
        raise TypeError('cutoff must be nonbool int')
    if not 1 <= cutoff <= 10:
        raise ValueError('cutoff must be between 1 and 10')
    if type(items) not in (list, tuple):
        raise TypeError('items must be a list or tuple')
    if not 1 <= len(items) <= 20:
        raise ValueError('item count must be between 1 and 20')
    rows = []
    for it in items:
        if type(it) not in (list, tuple) or len(it) != 3:
            raise ValueError('each item must be (name, weight, status)')
        name, w, s = it
        if type(name) is not str:
            raise TypeError('names must be str')
        if not 1 <= len(name) <= 40:
            raise ValueError('names must be 1 to 40 characters')
        if type(w) is not int or type(s) is not int:
            raise TypeError('weight and status must be nonbool int')
        if not 1 <= w <= 10:
            raise ValueError('weight must be between 1 and 10')
        if s not in (0, 1, 2):
            raise ValueError('status must be 0, 1 or 2')
        rows.append((name, w, s))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('item names must be unique')
    total = sum(r[1] for r in rows)
    return {'total_weight': total, 'done_share': Fraction(sum(r[1] for r in rows if r[2] == 2), total),
            'in_progress_share': Fraction(sum(r[1] for r in rows if r[2] == 1), total),
            'blockers': tuple(r[0] for r in rows if r[2] != 2 and r[1] >= cutoff),
            'ipo_validated': False, 'not_claimed': NOT_CLAIMED}


def offering_math(pre_shares, new_shares, price):
    for label, v, lo, hi in (('pre_shares', pre_shares, 1, 10 ** 10), ('new_shares', new_shares, 0, 10 ** 10),
                             ('price', price, 1, 10 ** 9)):
        if type(v) is not int:
            raise TypeError(label + ' must be nonbool int')
        if not lo <= v <= hi:
            raise ValueError('%s must be between %d and %d' % (label, lo, hi))
    post = pre_shares + new_shares
    return {'gross_proceeds': new_shares * price, 'pre_money': pre_shares * price, 'post_money': post * price,
            'existing_share': Fraction(pre_shares, post), 'new_investor_share': Fraction(new_shares, post),
            'ipo_validated': False, 'not_claimed': NOT_CLAIMED}
