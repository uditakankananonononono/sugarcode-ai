"""Row 1400, Climate Finance.

climate_split_fixture sums supplied mitigation x and adaptation y counts
and compares mitigation total with percent of combined total. Returns total,
mitigation, adaptation, target and gap Fraction strings, and meets. Zero
total meets by arithmetic convention. No verified climate impact,
climate-finance assessment, funding decision or financial advice is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 40, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: climate finance assessment, climate impact model, funding decision, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied mitigation/adaptation count target split, no climate-finance assessment'
NOT_CLAIMED = ('climate finance assessment', 'climate impact model', 'funding decision', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def climate_split_fixture(rows, percent=40):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(percent) is not int or not 0 <= percent <= 100:
        raise ValueError('percent must be a nonbool integer between 0 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    from fractions import Fraction as F
    total=sum(x+y for n,x,y in clean); actual=sum(x for n,x,y in clean)
    target=F(percent*total,100)
    return {'total':total,'mitigation':actual,'adaptation':total-actual,
            'target':str(target),'gap':str(max(target-actual,F(0))),'meets':actual>=target}
