"""Row 1425, Course Design.

course_credit_fixture computes load as supplied contact x plus twice
study y and counts complete per_credit blocks independently by row. Returns
sorted credits (label,complete,remainder), total complete credits,
unfinished nonzero remainders and load total. This abstract count rule is
not academic course design, real credit policy, accreditation compliance
or learning outcome validation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
per_credit defaults to 5, an exact int from 1 to 10.
Validation order: rows type, rows size, per_credit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: academic course design, accreditation compliance, learning outcome validation, production readiness.
"""

SCOPE = 'PARTIAL: converts supplied contact/study counts into abstract credits, no academic course design'
NOT_CLAIMED = ('academic course design', 'accreditation compliance', 'learning outcome validation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def course_credit_fixture(rows, per_credit=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(per_credit) is not int or not 1 <= per_credit <= 10:
        raise ValueError('per_credit must be a nonbool integer between 1 and 10')
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
    values=sorted((n,(x+2*y)//per_credit,(x+2*y)%per_credit) for n,x,y in clean)
    return {'credits':values,'total':sum(c for n,c,r in values),
            'unfinished':[n for n,c,r in values if r!=0],'load':sum(x+2*y for n,x,y in clean)}
