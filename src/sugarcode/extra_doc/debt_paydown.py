"""Row 693, Technical Debt Management: paydown plan within a capacity.

debt_paydown takes items, a list or tuple of 0 to 12 (name, cost, interest)
triples, and capacity, a nonbool int from 1 to 200 (default 20). A name is a
string of 1 to 12 characters, distinct across items. cost is a nonbool int from 1
to 100 and interest is a nonbool int from 0 to 50 (interest paid per sprint
while the debt remains). Items are ranked by interest per cost, highest first,
equal ratios keeping input order. Walking that ranking, an item is paid when
its cost still fits in the remaining capacity, otherwise it is skipped.
Returns paid (names in ranking order), skipped (names in ranking order), spent,
saved (interest of paid items) and remaining (interest of skipped items).
Checks, in this order: capacity, items type, items size, each triple, duplicate
names.
NOT_CLAIMED: real debt measurement, code quality, true interest rates,
optimal packing, production readiness.
"""
SCOPE = 'PARTIAL: greedy interest-per-cost ranking of supplied debt items, no code is measured'
NOT_CLAIMED = ('real debt measurement', 'code quality', 'true interest rates',
               'optimal packing', 'production readiness')


def debt_paydown(items, capacity=20):
    if type(capacity) is not int or not 1 <= capacity <= 200:
        raise ValueError('capacity must be a nonbool integer between 1 and 200')
    if type(items) not in (list, tuple):
        raise TypeError('items must be a list or tuple')
    if len(items) > 12:
        raise ValueError('items must contain at most 12 entries')
    rows = []
    for t in items:
        if type(t) not in (list, tuple) or len(t) != 3:
            raise ValueError('each item must be a (name, cost, interest) triple')
        name, cost, interest = t
        if type(name) is not str or not 1 <= len(name) <= 12:
            raise ValueError('each name must be a string of 1 to 12 characters')
        if type(cost) is not int or not 1 <= cost <= 100:
            raise ValueError('cost must be a nonbool integer between 1 and 100')
        if type(interest) is not int or not 0 <= interest <= 50:
            raise ValueError('interest must be a nonbool integer between 0 and 50')
        rows.append((name, cost, interest))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('names must be distinct')
    order = list(rows)
    for i in range(1, len(order)):
        cur = order[i]
        j = i - 1
        while j >= 0 and order[j][2] * cur[1] < cur[2] * order[j][1]:
            order[j + 1] = order[j]
            j -= 1
        order[j + 1] = cur
    left = capacity
    paid, skipped = [], []
    saved = remaining = 0
    for name, cost, interest in order:
        if cost <= left:
            left -= cost
            paid.append(name)
            saved += interest
        else:
            skipped.append(name)
            remaining += interest
    return {'paid': paid, 'skipped': skipped, 'spent': capacity - left,
            'saved': saved, 'remaining': remaining}
