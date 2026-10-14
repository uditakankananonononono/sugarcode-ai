"""Row 1490, Competency-Based Education.

competency_count_fixture caps supplied completed y at required x and
assigns credit counts per completed competency. Returns sorted competencies
(label,capped_completed,credits,gap), credits total, complete zero-gap labels
and remaining total. No competency education system, mastery verification,
actual credential award, skill assessment or recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
credit defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, credit, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: competency education system, mastery verification, credential award, production readiness.
"""

SCOPE = 'PARTIAL: supplied required/completed count competency credit, no competency education system'
NOT_CLAIMED = ('competency education system', 'mastery verification', 'credential award', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def competency_count_fixture(rows, credit=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(credit) is not int or not 1 <= credit <= 5:
        raise ValueError('credit must be a nonbool integer between 1 and 5')
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
    values=sorted((n,min(x,y),credit*min(x,y),max(x-y,0)) for n,x,y in clean)
    return {'competencies':values,'credits':sum(c for n,a,c,g in values),
            'complete':[n for n,a,c,g in values if g==0],'remaining':sum(g for n,a,c,g in values)}
