"""Row 1259, Environmental Law.

environment_limit_fixture subtracts abstract count x and buffer from supplied
limit y. Returns sorted margins, negative and zero labels and minimum margin.
No emission units, environmental impact, statutory requirement, compliance
or real-world safety are measured or verified.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
buffer defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, buffer, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: environmental law, legal compliance, environmental impact, real emissions or safety, production readiness.
"""

SCOPE = 'PARTIAL: inventories supplied abstract limit margins, no environmental law analysis'
NOT_CLAIMED = ('environmental law', 'legal compliance', 'environmental impact', 'real emissions or safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def environment_limit_fixture(rows, buffer=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(buffer) is not int or not 0 <= buffer <= 10:
        raise ValueError('buffer must be a nonbool integer between 0 and 10')
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
    margins=[(n,y-x-buffer) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'margins':margins,'negative':[n for n,v in margins if v<0],
            'zero':[n for n,v in margins if v==0],'minimum':min(v for n,v in margins)}
