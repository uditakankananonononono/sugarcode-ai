"""Row 1355, Jump Diffusion.

jump_event_fixture adds supplied y to base x when y meets threshold,
otherwise retains x. Returns sorted values, jumps labels meeting threshold
including zero at zero threshold, and total. No diffusion, random event,
probability, market dynamics, calibration or investment advice is provided.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
threshold defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: diffusion process, random jump simulation, market calibration, investment advice, production readiness.
"""

SCOPE = 'PARTIAL: tallies supplied count jumps at a threshold, no diffusion process'
NOT_CLAIMED = ('diffusion process', 'random jump simulation', 'market calibration', 'investment advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def jump_event_fixture(rows, threshold=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 0 <= threshold <= 10:
        raise ValueError('threshold must be a nonbool integer between 0 and 10')
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
    values=[(n,x+y if y>=threshold else x) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'values':values,'jumps':[n for n,x,y in sorted(clean,key=lambda r:r[0]) if y>=threshold],
            'total':sum(v for n,v in values)}
