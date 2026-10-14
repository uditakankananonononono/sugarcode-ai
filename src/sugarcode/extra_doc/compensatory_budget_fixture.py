"""Row 1516, Compensatory Education.

compensatory_budget_fixture adds supplement to supplied resource count y
and caps coverage at shortfall count x. Returns sorted coverage
(label,covered,gap), covered zero-gap labels, gap total and supplement.
No compensatory education judgment, learner needs inference, real resource
award, social inference, effectiveness or educational recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
supplement defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, supplement, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: compensatory education judgment, learner needs inference, resource award, production readiness.
"""

SCOPE = 'PARTIAL: supplied shortfall/resource count capped supplement, no compensatory education judgment'
NOT_CLAIMED = ('compensatory education judgment', 'learner needs inference', 'resource award', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def compensatory_budget_fixture(rows, supplement=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(supplement) is not int or not 0 <= supplement <= 5:
        raise ValueError('supplement must be a nonbool integer between 0 and 5')
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
    values=sorted((n,min(x,y+supplement),max(x-y-supplement,0)) for n,x,y in clean)
    return {'coverage':values,'covered':[n for n,c,g in values if g==0],
            'gap':sum(g for n,c,g in values),'supplement':supplement}
