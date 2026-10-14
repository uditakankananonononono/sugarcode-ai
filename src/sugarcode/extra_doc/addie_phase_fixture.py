"""Row 1428, ADDIE Model.

addie_phase_fixture expands supplied analysis count x and development
count y into the fixed phase tuple (x,x plus one,y,y plus one,evaluation)
for analysis, design, development, implementation and evaluation. Returns
sorted phases (label,tuple,total), aggregate total and evaluation. These
are fixture budgets, not the ADDIE instructional-design process, pedagogical
validation, actual learning evaluation or educational recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
evaluation defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, evaluation, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: instructional design process, pedagogical validation, learning evaluation, production readiness.
"""

SCOPE = 'PARTIAL: expands supplied phase-count budgets into fixed ADDIE-stage bookkeeping, no instructional-design process'
NOT_CLAIMED = ('instructional design process', 'pedagogical validation', 'learning evaluation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def addie_phase_fixture(rows, evaluation=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(evaluation) is not int or not 0 <= evaluation <= 5:
        raise ValueError('evaluation must be a nonbool integer between 0 and 5')
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
    values=[]
    for n,analysis,development in sorted(clean,key=lambda r:r[0]):
        phases=(analysis,analysis+1,development,development+1,evaluation)
        values.append((n,phases,sum(phases)))
    return {'phases':values,'total':sum(t for n,p,t in values),'evaluation':evaluation}
