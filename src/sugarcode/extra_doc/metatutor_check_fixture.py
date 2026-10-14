"""Row 1502, Metacognitive Tutoring.

metatutor_check_fixture compares supplied check count y to checks_per_plan
times plan count x. Returns sorted signed deficits, needs_checks positive
labels, needed total positive deficits and surplus total negative magnitudes.
No metacognitive tutoring, learner diagnosis, planning correctness,
reflection quality validation or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
checks_per_plan defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, checks_per_plan, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: metacognitive tutoring, learner diagnosis, reflection quality validation, production readiness.
"""

SCOPE = 'PARTIAL: supplied plan/check count reflection budget, no metacognitive tutoring'
NOT_CLAIMED = ('metacognitive tutoring', 'learner diagnosis', 'reflection quality validation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def metatutor_check_fixture(rows, checks_per_plan=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(checks_per_plan) is not int or not 1 <= checks_per_plan <= 5:
        raise ValueError('checks_per_plan must be a nonbool integer between 1 and 5')
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
    values=sorted((n,checks_per_plan*x-y) for n,x,y in clean)
    return {'deficits':values,'needs_checks':[n for n,d in values if d>0],
            'needed':sum(max(d,0) for n,d in values),'surplus':sum(max(-d,0) for n,d in values)}
