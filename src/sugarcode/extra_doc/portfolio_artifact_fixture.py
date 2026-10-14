"""Row 1483, Portfolio Assessment.

portfolio_artifact_fixture requires positive supplied artifact count x
and reflection count y meeting minimum_reflections. Returns sorted included
booleans, passing labels, no_artifacts and artifacts total. No actual
portfolio assessment, artifact quality judgment, reflection depth validation,
learner evaluation, file retrieval or educational recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum_reflections defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, minimum_reflections, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: portfolio assessment, artifact quality judgment, learner evaluation, production readiness.
"""

SCOPE = 'PARTIAL: supplied artifact/reflection count inclusion screen, no portfolio assessment'
NOT_CLAIMED = ('portfolio assessment', 'artifact quality judgment', 'learner evaluation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def portfolio_artifact_fixture(rows, minimum_reflections=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum_reflections) is not int or not 0 <= minimum_reflections <= 10:
        raise ValueError('minimum_reflections must be a nonbool integer between 0 and 10')
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
    values=sorted((n,x>0 and y>=minimum_reflections) for n,x,y in clean)
    return {'included':values,'passing':[n for n,v in values if v],
            'no_artifacts':sorted(n for n,x,y in clean if x==0),'artifacts':sum(x for n,x,y in clean)}
