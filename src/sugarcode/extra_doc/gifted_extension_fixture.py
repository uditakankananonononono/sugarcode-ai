"""Row 1514, Gifted Education.

gifted_extension_fixture computes supplied completed y minus target x
count floored at zero and multiplies extension count by multiplier. Returns
sorted extensions (label,extra,budget), eligible positive extra labels,
budget and extra totals. No giftedness assessment, learner diagnosis,
ability inference, actual extension activities or pedagogical recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
multiplier defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, multiplier, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: giftedness assessment, learner diagnosis, pedagogical recommendation, production readiness.
"""

SCOPE = 'PARTIAL: supplied target/completed count extension budget, no giftedness assessment'
NOT_CLAIMED = ('giftedness assessment', 'learner diagnosis', 'pedagogical recommendation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def gifted_extension_fixture(rows, multiplier=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(multiplier) is not int or not 1 <= multiplier <= 5:
        raise ValueError('multiplier must be a nonbool integer between 1 and 5')
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
    values=sorted((n,max(y-x,0),multiplier*max(y-x,0)) for n,x,y in clean)
    return {'extensions':values,'eligible':[n for n,e,b in values if e>0],
            'budget':sum(b for n,e,b in values),'extra':sum(e for n,e,b in values)}
