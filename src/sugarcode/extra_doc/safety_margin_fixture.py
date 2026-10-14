"""Row 1533, Safety Engineering.

safety_margin_fixture subtracts supplied demand x and reserve from
supplied capacity y counts. Returns sorted margins, negative shortfalls,
zero at_limit labels and minimum margin. This is abstract margin bookkeeping,
not safety judgement, hazard detection, biological containment, standards
compliance, physical capacity validation or engineering certification.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
reserve defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, reserve, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: safety judgement, hazard detection, standards compliance, physical capacity validation, production readiness.
"""

SCOPE = 'PARTIAL: supplied demand/capacity count margin, no safety judgement'
NOT_CLAIMED = ('safety judgement', 'hazard detection', 'standards compliance', 'physical capacity validation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def safety_margin_fixture(rows, reserve=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(reserve) is not int or not 0 <= reserve <= 5:
        raise ValueError('reserve must be a nonbool integer between 0 and 5')
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
    margins=sorted((n,y-x-reserve) for n,x,y in clean)
    return {'margins':margins,'shortfalls':[n for n,v in margins if v<0],
            'at_limit':[n for n,v in margins if v==0],'minimum':min(v for n,v in margins)}
