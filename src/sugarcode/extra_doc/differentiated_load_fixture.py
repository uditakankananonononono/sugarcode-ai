"""Row 1432, Differentiated Instruction.

differentiated_load_fixture assigns supplied level count x below cutoff
to foundation and others to extension. Foundation gets base activity count
y plus cutoff deficit, extension gets y. Returns sorted groups
(label,tier,activity_count), foundation labels and total_activities.
No differentiated pedagogy, learner assessment, activity content, learning
effectiveness or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cutoff defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, cutoff, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: differentiated pedagogy, learner assessment, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied group-level activity-count tiers, no differentiated pedagogy'
NOT_CLAIMED = ('differentiated pedagogy', 'learner assessment', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def differentiated_load_fixture(rows, cutoff=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cutoff) is not int or not 0 <= cutoff <= 10:
        raise ValueError('cutoff must be a nonbool integer between 0 and 10')
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
    values=sorted((n,'foundation' if x<cutoff else 'extension',y+(cutoff-x if x<cutoff else 0)) for n,x,y in clean)
    return {'groups':values,'foundation':[n for n,t,v in values if t=='foundation'],
            'total_activities':sum(v for n,t,v in values)}
