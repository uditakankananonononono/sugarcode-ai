"""Row 1487, Assessment as Learning.

aslearning_reflect_fixture pairs supplied self-check x and reflection y
counts and counts discrepancy. Returns sorted checks (label,paired,unpaired),
balanced equal counts meeting minimum paired, paired and unpaired totals.
No assessment-as-learning process, reflection quality, metacognitive
diagnosis, learning effectiveness or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: assessment as learning process, metacognitive diagnosis, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied self-check/reflection count discrepancy, no assessment-as-learning process'
NOT_CLAIMED = ('assessment as learning process', 'metacognitive diagnosis', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def aslearning_reflect_fixture(rows, minimum=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 10:
        raise ValueError('minimum must be a nonbool integer between 0 and 10')
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
    values=sorted((n,min(x,y),abs(x-y)) for n,x,y in clean)
    return {'checks':values,'balanced':[n for n,c,g in values if g==0 and c>=minimum],
            'paired':sum(c for n,c,g in values),'unpaired':sum(g for n,c,g in values)}
