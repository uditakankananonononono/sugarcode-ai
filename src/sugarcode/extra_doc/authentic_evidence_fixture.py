"""Row 1481, Authentic Assessment.

authentic_evidence_fixture assigns evidence_per_task requirements to
supplied task count x, caps supplied evidence count y at requirements and
counts gaps. Returns sorted evidence (label,accepted,missing), covered,
missing and accepted totals. No authentic assessment validity, real-world
task judgment, evidence quality, learner evaluation or recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
evidence_per_task defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, evidence_per_task, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: authentic assessment validity, real world task judgment, learner evaluation, production readiness.
"""

SCOPE = 'PARTIAL: supplied task/evidence count coverage, no authentic assessment validity'
NOT_CLAIMED = ('authentic assessment validity', 'real world task judgment', 'learner evaluation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def authentic_evidence_fixture(rows, evidence_per_task=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(evidence_per_task) is not int or not 1 <= evidence_per_task <= 5:
        raise ValueError('evidence_per_task must be a nonbool integer between 1 and 5')
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
    values=sorted((n,min(evidence_per_task*x,y),max(evidence_per_task*x-y,0)) for n,x,y in clean)
    return {'evidence':values,'covered':[n for n,e,g in values if g==0],
            'missing':sum(g for n,e,g in values),'accepted':sum(e for n,e,g in values)}
