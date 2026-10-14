"""Row 1508, Global Competence.

global_context_fixture requires tasks_per_context times supplied context
count x and caps supplied completed task count y at requirement. Returns
sorted coverage (label,accepted,gap), covered zero-gap labels, gap and accepted
totals. No global-competence assessment, actual context representation,
cultural judgment, learning effectiveness or recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tasks_per_context defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, tasks_per_context, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: global competence assessment, cultural judgment, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied context/task count coverage gaps, no global-competence assessment'
NOT_CLAIMED = ('global competence assessment', 'cultural judgment', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def global_context_fixture(rows, tasks_per_context=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tasks_per_context) is not int or not 1 <= tasks_per_context <= 5:
        raise ValueError('tasks_per_context must be a nonbool integer between 1 and 5')
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
    values=sorted((n,min(tasks_per_context*x,y),max(tasks_per_context*x-y,0)) for n,x,y in clean)
    return {'coverage':values,'covered':[n for n,c,g in values if g==0],
            'gap':sum(g for n,c,g in values),'accepted':sum(c for n,c,g in values)}
