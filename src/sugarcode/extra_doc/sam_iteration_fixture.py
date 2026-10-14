"""Row 1429, SAM Model.

sam_iteration_fixture expands supplied prototype count x and review
count y over iterations. Each iteration tuple is (one-based index,x plus
zero-based index,y). Returns sorted iterations (label,list), prototype_total
and review_total. This fixed count-budget schedule does not implement the
SAM instructional-design process, prototype generation or pedagogical validation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
iterations defaults to 3, an exact int from 1 to 5.
Validation order: rows type, rows size, iterations, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: SAM design process, pedagogical validation, prototype generation, production readiness.
"""

SCOPE = 'PARTIAL: accounts supplied prototype/review counts over fixed iterations, no SAM design process'
NOT_CLAIMED = ('SAM design process', 'pedagogical validation', 'prototype generation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def sam_iteration_fixture(rows, iterations=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(iterations) is not int or not 1 <= iterations <= 5:
        raise ValueError('iterations must be a nonbool integer between 1 and 5')
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
    values=sorted((n,[(i+1,x+i,y) for i in range(iterations)]) for n,x,y in clean)
    return {'iterations':values,'prototype_total':sum(x+i for n,x,y in clean for i in range(iterations)),
            'review_total':iterations*sum(y for n,x,y in clean)}
