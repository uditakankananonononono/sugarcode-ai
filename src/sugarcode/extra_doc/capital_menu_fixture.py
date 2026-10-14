"""Row 1322, Capital Budgeting.

capital_menu_fixture filters positive abstract cost x within budget and
ranks value count y per cost descending then label. Returns menu Fraction
strings, best all maximum labels or empty and outside excluded labels.
No real money, investment return, financial advice or capital commitment
is assessed, recommended or made.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
1 to 10; bool and all subclasses are refused.
budget defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, budget, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: capital budgeting recommendation, real investment returns, financial advice, capital commitment, production readiness.
"""

SCOPE = 'PARTIAL: ranks abstract supplied value/cost menu, no capital budgeting recommendation'
NOT_CLAIMED = ('capital budgeting recommendation', 'real investment returns', 'financial advice', 'capital commitment', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def capital_menu_fixture(rows, budget=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(budget) is not int or not 0 <= budget <= 10:
        raise ValueError('budget must be a nonbool integer between 0 and 10')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 1 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 1 and 10')
        if type(y) is not int or not 1 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 1 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    menu=[(n,F(y,x)) for n,x,y in clean if x<=budget]
    menu.sort(key=lambda r:(-r[1],r[0]))
    return {'menu':[(n,str(v)) for n,v in menu],
            'best':[n for n,v in menu if v==menu[0][1]] if menu else [],
            'outside':sorted(n for n,x,y in clean if x>budget)}
