"""Row 1486, Assessment for Learning.

forlearning_gain_fixture subtracts supplied baseline x from latest y
count and computes deficit to baseline plus gain. Returns sorted progress
(label,difference,remaining), meeting zero-deficit labels, remaining total
and net_gain. No assessment-for-learning process, intervention validation,
causal learning inference, learner evaluation or recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
gain defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, gain, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: assessment for learning process, causal learning inference, learner evaluation, production readiness.
"""

SCOPE = 'PARTIAL: supplied baseline/latest count improvement targets, no assessment-for-learning process'
NOT_CLAIMED = ('assessment for learning process', 'causal learning inference', 'learner evaluation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def forlearning_gain_fixture(rows, gain=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(gain) is not int or not 0 <= gain <= 10:
        raise ValueError('gain must be a nonbool integer between 0 and 10')
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
    values=sorted((n,y-x,max(x+gain-y,0)) for n,x,y in clean)
    return {'progress':values,'meeting':[n for n,d,g in values if g==0],
            'remaining':sum(g for n,d,g in values),'net_gain':sum(d for n,d,g in values)}
