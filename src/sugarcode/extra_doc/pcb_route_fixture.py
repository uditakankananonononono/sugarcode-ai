"""Row 1582, PCB Design.

pcb_route_fixture adds supplied trace x count to via_cost times via y
count. Returns sorted route_costs, total, via_free zero-via labels and
via_cost. No PCB design, physical layout validation, electrical safety,
manufacturing rules, physical units or real routing instructions.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
via_cost defaults to 3, an exact int from 1 to 5.
Validation order: rows type, rows size, via_cost, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: PCB design, physical layout validation, electrical safety, manufacturing rules, production readiness.
"""

SCOPE = 'PARTIAL: supplied trace/via count route budget, no PCB design'
NOT_CLAIMED = ('PCB design', 'physical layout validation', 'electrical safety', 'manufacturing rules', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def pcb_route_fixture(rows, via_cost=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(via_cost) is not int or not 1 <= via_cost <= 5:
        raise ValueError('via_cost must be a nonbool integer between 1 and 5')
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
    values=sorted((n,x+via_cost*y) for n,x,y in clean)
    return {'route_costs':values,'total':sum(v for n,v in values),'via_free':sorted(n for n,x,y in clean if y==0),
            'via_cost':via_cost}
