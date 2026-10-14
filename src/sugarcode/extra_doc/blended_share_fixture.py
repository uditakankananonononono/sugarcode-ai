"""Row 1451, Blended Learning.

blended_share_fixture divides supplied online count x by online plus
in-person count y, undefined when both zero. Returns sorted online_shares
Fraction strings or None, meeting inclusive percent, both_modes requiring
both positive and empty. No blended-learning design, content validation,
actual course delivery or learning-effectiveness claim is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
percent defaults to 40, an exact int from 0 to 100.
Validation order: rows type, rows size, percent, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: blended learning design, learning effectiveness, course delivery, production readiness.
"""

SCOPE = 'PARTIAL: supplied online/in-person count mix share, no blended-learning design'
NOT_CLAIMED = ('blended learning design', 'learning effectiveness', 'course delivery', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def blended_share_fixture(rows, percent=40):
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
    values=sorted((n,F(x,x+y) if x+y else None) for n,x,y in clean)
    return {'online_shares':[(n,str(v)) if v is not None else (n,None) for n,v in values],
            'meeting':[n for n,v in values if v is not None and v>=F(percent,100)],
            'both_modes':sorted(n for n,x,y in clean if x>0 and y>0),'empty':[n for n,v in values if v is None]}
