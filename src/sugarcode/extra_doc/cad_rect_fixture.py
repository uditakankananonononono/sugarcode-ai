"""Row 1521, CAD Modeling.

cad_rect_fixture treats supplied x and y counts as rectangle sides and
depth as common extrusion count. Returns sorted solids
(label,area,perimeter,volume), volume and area totals, degenerate labels with
zero area or depth. No physical units, CAD model/file generation, real
geometry, manufacturability assessment or engineering safety claim.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
depth defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, depth, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: CAD model generation, physical units, manufacturability, production readiness.
"""

SCOPE = 'PARTIAL: supplied abstract rectangle extrusion counts, no CAD model generation'
NOT_CLAIMED = ('CAD model generation', 'physical units', 'manufacturability', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cad_rect_fixture(rows, depth=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(depth) is not int or not 0 <= depth <= 10:
        raise ValueError('depth must be a nonbool integer between 0 and 10')
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
    values=sorted((n,x*y,2*(x+y),x*y*depth) for n,x,y in clean)
    return {'solids':values,'volume':sum(v for n,a,p,v in values),'area':sum(a for n,a,p,v in values),
            'degenerate':[n for n,a,p,v in values if a==0 or depth==0]}
