"""Row 1498, Computer-Assisted Instruction.

cai_retry_fixture caps supplied errors y at exercise count x and allows
at most retry_cap retries. Returns sorted retry (label,capped_errors,
allowed,deferred), total allowed, deferred total and error_free zero capped
error labels. No actual computer-assisted instruction, exercise generation,
error validation, learning effectiveness or educational recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
retry_cap defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, retry_cap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: computer assisted instruction, content generation, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied exercise/error count retry allocation, no computer-assisted instruction'
NOT_CLAIMED = ('computer assisted instruction', 'content generation', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def cai_retry_fixture(rows, retry_cap=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(retry_cap) is not int or not 0 <= retry_cap <= 10:
        raise ValueError('retry_cap must be a nonbool integer between 0 and 10')
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
    values=sorted((n,min(x,y),min(min(x,y),retry_cap),max(min(x,y)-retry_cap,0)) for n,x,y in clean)
    return {'retry':values,'total':sum(a for n,e,a,d in values),'deferred':sum(d for n,e,a,d in values),
            'error_free':sorted(n for n,x,y in clean if min(x,y)==0)}
