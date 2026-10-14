"""Row 1477, Automated Feedback.

feedback_gap_fixture formats supplied target x minus achieved y count
deficit floored at zero into fixed text, rounding count steps up by step.
Returns sorted messages (label,text), complete labels meeting target and
total_steps. No substantive feedback judgment, text analysis, learner
diagnosis, semantic quality or educational recommendation is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
step defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, step, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: substantive feedback judgment, text analysis, learner diagnosis, production readiness.
"""

SCOPE = 'PARTIAL: formats supplied target/achieved count deficit feedback, no substantive feedback judgment'
NOT_CLAIMED = ('substantive feedback judgment', 'text analysis', 'learner diagnosis', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def feedback_gap_fixture(rows, step=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(step) is not int or not 1 <= step <= 5:
        raise ValueError('step must be a nonbool integer between 1 and 5')
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
    values=sorted((n,f'{n}: add {max(x-y,0)} counts in {(max(x-y,0)+step-1)//step} steps') for n,x,y in clean)
    return {'messages':values,'complete':sorted(n for n,x,y in clean if y>=x),
            'total_steps':sum((max(x-y,0)+step-1)//step for n,x,y in clean)}
