"""Row 1515, Remedial Education.

remedial_repeat_fixture subtracts supplied current count y from target x,
floors gap at zero and allocates repetitions per gap. Returns sorted repeats
(label,gap,repetition_count), no_gap labels, total repetitions and gap.
No remedial diagnosis, learner assessment, actual remediation, progress
verification, learning effectiveness or educational recommendation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
repetitions defaults to 3, an exact int from 1 to 5.
Validation order: rows type, rows size, repetitions, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: remedial diagnosis, learner assessment, learning effectiveness, production readiness.
"""

SCOPE = 'PARTIAL: supplied target/current count repetition budgets, no remedial diagnosis'
NOT_CLAIMED = ('remedial diagnosis', 'learner assessment', 'learning effectiveness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def remedial_repeat_fixture(rows, repetitions=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(repetitions) is not int or not 1 <= repetitions <= 5:
        raise ValueError('repetitions must be a nonbool integer between 1 and 5')
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
    values=sorted((n,max(x-y,0),repetitions*max(x-y,0)) for n,x,y in clean)
    return {'repeats':values,'no_gap':[n for n,g,r in values if g==0],
            'total':sum(r for n,g,r in values),'gap':sum(g for n,g,r in values)}
