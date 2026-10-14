"""Row 1551, Response Surface Methodology.

response_surface_fixture evaluates the fixed supplied count polynomial
x squared plus y squared plus interaction times x times y. Returns sorted
responses, highest tied labels, total and interaction. No response surface
fitting, experimental design, statistical inference, physical response
prediction, optimization advice or engineering certification is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
interaction defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, interaction, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: response surface fitting, experimental design, statistical inference, physical response prediction, production readiness.
"""

SCOPE = 'PARTIAL: fixed supplied count polynomial surface, no response surface fitting'
NOT_CLAIMED = ('response surface fitting', 'experimental design', 'statistical inference', 'physical response prediction', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def response_surface_fixture(rows, interaction=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(interaction) is not int or not 0 <= interaction <= 5:
        raise ValueError('interaction must be a nonbool integer between 0 and 5')
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
    values=sorted((n,x*x+y*y+interaction*x*y) for n,x,y in clean)
    top=max(v for n,v in values)
    return {'responses':values,'highest':[n for n,v in values if v==top],
            'total':sum(v for n,v in values),'interaction':interaction}
