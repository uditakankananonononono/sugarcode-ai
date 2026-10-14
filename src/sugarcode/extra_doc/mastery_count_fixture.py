"""Row 1491, Mastery Learning.

mastery_count_fixture computes supplied goal x minus current y deficit,
floors at zero and rounds retry count up by gain_per_retry. Returns sorted
retries, already zero-retry labels, total and gain_per_retry. The gain is
assumed fixture bookkeeping, not actual learning progress. No mastery
learning system, mastery verification or learning-effectiveness claim.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
gain_per_retry defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, gain_per_retry, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: mastery learning system, mastery verification, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied goal/current count retry budget, no mastery learning system'
NOT_CLAIMED = ('mastery learning system', 'mastery verification', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def mastery_count_fixture(rows, gain_per_retry=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(gain_per_retry) is not int or not 1 <= gain_per_retry <= 5:
        raise ValueError('gain_per_retry must be a nonbool integer between 1 and 5')
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
    values=sorted((n,(max(x-y,0)+gain_per_retry-1)//gain_per_retry) for n,x,y in clean)
    return {'retries':values,'already':[n for n,v in values if v==0],
            'total':sum(v for n,v in values),'gain_per_retry':gain_per_retry}
