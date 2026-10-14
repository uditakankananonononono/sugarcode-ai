"""Row 1967, Transfer Learning.

transfer_overlap_counts divides supplied shared x feature count by
shared plus new y count, with None for empty declarations. Returns sorted
reuse Fraction-string-or-None pairs, selected inclusive percent labels
excluding empty declarations, new_total and empty labels. Counts do not
establish feature compatibility, actual reuse or learning. No transfer
learning, model training, feature compatibility or task performance claim.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: transfer learning, model training, feature compatibility, task performance, production readiness.
"""

SCOPE = 'PARTIAL: supplied shared/new feature counts and reuse ratio, no transfer learning'
NOT_CLAIMED = ('transfer learning', 'model training', 'feature compatibility', 'task performance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def transfer_overlap_counts(rows, percent=50):
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
    ratios=sorted((n,F(x,x+y) if x+y else None) for n,x,y in clean)
    return {'reuse':[(n,str(v) if v is not None else None) for n,v in ratios],
            'selected':[n for n,v in ratios if v is not None and v>=F(percent,100)],
            'new_total':sum(y for n,x,y in clean),'empty':[n for n,v in ratios if v is None]}
