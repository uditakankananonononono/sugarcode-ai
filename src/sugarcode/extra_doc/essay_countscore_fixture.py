"""Row 1476, Automated Essay Scoring.

essay_countscore_fixture combines supplied claim count x twice and
evidence count y three times, caps at cap. Returns sorted scores, capped
strictly beyond cap before limiting, total and cap. No essays are read;
counts are unverified. No actual essay scoring, text analysis, grading
validity, semantic evidence quality or student judgment is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cap defaults to 10, an exact int from 0 to 20.
Validation order: rows type, rows size, cap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: essay scoring, text analysis, grading validity, production readiness.
"""

SCOPE = 'PARTIAL: supplied claim/evidence count bounded score, no essay scoring'
NOT_CLAIMED = ('essay scoring', 'text analysis', 'grading validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def essay_countscore_fixture(rows, cap=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cap) is not int or not 0 <= cap <= 20:
        raise ValueError('cap must be a nonbool integer between 0 and 20')
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
    values=sorted((n,min(2*x+3*y,cap)) for n,x,y in clean)
    return {'scores':values,'capped':sorted(n for n,x,y in clean if 2*x+3*y>cap),
            'total':sum(v for n,v in values),'cap':cap}
