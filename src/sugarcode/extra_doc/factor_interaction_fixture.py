"""Row 1549, Design of Experiments.

factor_interaction_fixture computes supplied factor count product minus
baseline times their sum. Returns sorted contrasts, positive labels, total
and baseline. No experimental design, causal inference, statistical
significance, physical experiment execution, treatment selection or
scientific validation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
baseline defaults to 2, an exact int from 0 to 5.
Validation order: rows type, rows size, baseline, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: experimental design, causal inference, statistical significance, physical experiment execution, production readiness.
"""

SCOPE = 'PARTIAL: supplied factor count interaction contrast, no experimental design'
NOT_CLAIMED = ('experimental design', 'causal inference', 'statistical significance', 'physical experiment execution', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def factor_interaction_fixture(rows, baseline=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(baseline) is not int or not 0 <= baseline <= 5:
        raise ValueError('baseline must be a nonbool integer between 0 and 5')
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
    values=sorted((n,x*y-baseline*(x+y)) for n,x,y in clean)
    return {'contrasts':values,'positive':[n for n,v in values if v>0],
            'total':sum(v for n,v in values),'baseline':baseline}
