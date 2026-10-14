"""Row 1467, Knowledge Tracing.

knowledge_increment_fixture starts at initial, adds supplied success x
count and subtracts twice failure y count in label order, clamping to zero
through ten at every row. Returns trace, final, zero and ceiling labels.
This is a deterministic bounded accumulator, not a knowledge-tracing model,
mastery probability, learner diagnosis or actual skill validation.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
initial defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, initial, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: knowledge tracing model, mastery probability, learner diagnosis, production readiness.
"""

SCOPE = 'PARTIAL: supplied success/failure count running accumulator, no knowledge-tracing model'
NOT_CLAIMED = ('knowledge tracing model', 'mastery probability', 'learner diagnosis', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def knowledge_increment_fixture(rows, initial=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(initial) is not int or not 0 <= initial <= 10:
        raise ValueError('initial must be a nonbool integer between 0 and 10')
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
    state=initial; values=[]
    for n,success,failure in sorted(clean,key=lambda r:r[0]):
        state=min(10,max(0,state+success-2*failure)); values.append((n,state))
    return {'trace':values,'final':state,'zero':[n for n,v in values if v==0],
            'ceiling':[n for n,v in values if v==10]}
