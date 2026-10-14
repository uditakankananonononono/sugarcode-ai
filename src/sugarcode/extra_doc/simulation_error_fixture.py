"""Row 1459, Simulation-Based Learning.

simulation_error_fixture compares supplied target x and actual y counts,
computes absolute error and positive remaining tolerance as score. Returns
sorted results (label,error,score), passing inclusive tolerance, score total
and error total. A boundary pass can have zero score. No simulation-based
pedagogy, simulation generation, skill validation or real learning claim.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: simulation based pedagogy, simulation generation, skill validation, production readiness.
"""

SCOPE = 'PARTIAL: supplied simulation target/actual count tolerance score, no simulation-based pedagogy'
NOT_CLAIMED = ('simulation based pedagogy', 'simulation generation', 'skill validation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def simulation_error_fixture(rows, tolerance=2):
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
    values=sorted((n,abs(x-y),max(tolerance-abs(x-y),0)) for n,x,y in clean)
    return {'results':values,'passing':[n for n,e,s in values if e<=tolerance],
            'score':sum(s for n,e,s in values),'error':sum(e for n,e,s in values)}
