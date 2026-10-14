"""Row 1509, Cultural Competence.

cultural_count_fixture computes minimum and absolute difference of
supplied knowledge x and practice y abstract counts. Returns sorted balance
(label,paired,gap), meeting inclusive minimum paired, equal zero-gap labels
and paired total. No cultural-competence judgment, culture identification,
knowledge validation, social inference or learning effectiveness is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: cultural competence judgment, culture identification, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied knowledge/practice count balance screen, no cultural-competence judgment'
NOT_CLAIMED = ('cultural competence judgment', 'culture identification', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cultural_count_fixture(rows, minimum=3):
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
    return {'balance':values,'meeting':[n for n,m,g in values if m>=minimum],
            'equal':[n for n,m,g in values if g==0],'paired':sum(m for n,m,g in values)}
