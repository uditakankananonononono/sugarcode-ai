"""Row 1526, Fatigue Analysis.

fatigue_damage_fixture multiplies supplied cycle count x by amplitude
count y squared as an abstract proxy and sums it. Returns sorted
contributions, damage total, exceeds strictly above limit and signed margin.
No fatigue-life model, stress-cycle curve, material calibration, physical
units, crack evolution, design certification or engineering safety claim.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
limit defaults to 20, an exact int from 0 to 100.
Validation order: rows type, rows size, limit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: fatigue life model, material calibration, physical units, engineering safety, production readiness.
"""

SCOPE = 'PARTIAL: supplied cycle/amplitude count cumulative damage proxy, no fatigue-life model'
NOT_CLAIMED = ('fatigue life model', 'material calibration', 'physical units', 'engineering safety', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def fatigue_damage_fixture(rows, limit=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(limit) is not int or not 0 <= limit <= 100:
        raise ValueError('limit must be a nonbool integer between 0 and 100')
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
    values=sorted((n,x*y*y) for n,x,y in clean)
    damage=sum(v for n,v in values)
    return {'contributions':values,'damage':damage,'exceeds':damage>limit,'margin':limit-damage}
