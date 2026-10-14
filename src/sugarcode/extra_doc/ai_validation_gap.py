"""Row 1962, AI Validation.

ai_validation_gap subtracts supplied holdout pass y count from supplied
development pass x count. Returns sorted gaps and label lists stable for
inclusive absolute tolerance, development_higher and holdout_higher for
strict respective excesses. Counts have no sample denominator and are not
accuracy estimates. No AI validation, generalization estimate, statistical
confidence, dataset independence or model correctness is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: AI validation, generalization estimate, statistical confidence, model correctness, production readiness.
"""

SCOPE = 'PARTIAL: supplied development/holdout pass count gap, no AI validation'
NOT_CLAIMED = ('AI validation', 'generalization estimate', 'statistical confidence', 'model correctness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ai_validation_gap(rows, tolerance=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tolerance) is not int or not 0 <= tolerance <= 10:
        raise ValueError('tolerance must be a nonbool integer between 0 and 10')
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
    gaps=sorted((n,x-y) for n,x,y in clean)
    return {'gaps':gaps,'stable':[n for n,v in gaps if abs(v)<=tolerance],
            'development_higher':[n for n,v in gaps if v>tolerance],
            'holdout_higher':[n for n,v in gaps if v<-tolerance]}
