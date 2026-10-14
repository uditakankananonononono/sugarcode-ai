"""Row 1431, Universal Design for Learning.

udl_channel_fixture screens two supplied abstract access-channel counts
x and y against minimum independently. Returns sorted gaps (label,first_gap,
second_gap), both_ready, needed sum and one_ready exactly one zero-gap.
No UDL pedagogical design, accessibility certification, accommodation
selection, learner needs inference or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: UDL pedagogical design, accessibility certification, learner needs inference, production readiness.
"""

SCOPE = 'PARTIAL: supplied paired access-channel count gaps, no UDL pedagogical design'
NOT_CLAIMED = ('UDL pedagogical design', 'accessibility certification', 'learner needs inference', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def udl_channel_fixture(rows, minimum=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 5:
        raise ValueError('minimum must be a nonbool integer between 0 and 5')
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
    values=sorted((n,max(minimum-x,0),max(minimum-y,0)) for n,x,y in clean)
    return {'gaps':values,'both_ready':[n for n,a,b in values if a==0 and b==0],
            'needed':sum(a+b for n,a,b in values),'one_ready':[n for n,a,b in values if (a==0)!=(b==0)]}
