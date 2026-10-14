"""Row 1972, Chain-of-Thought.

declared_step_budget allocates up to budget counts to supplied pending
y steps per record, adding that count to supplied completed x count.
Returns sorted progress pairs, pending remainder pairs, complete zero
remainder labels and executed_count. This is arithmetic on declared counts:
no actual steps are executed or reasoned about. No reasoning trace
generation, reasoning validity, model inference or answer correctness.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
budget defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, budget, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: reasoning trace generation, reasoning validity, model inference, answer correctness, production readiness.
"""

SCOPE = 'PARTIAL: supplied completed/pending step count budget, no reasoning trace generation'
NOT_CLAIMED = ('reasoning trace generation', 'reasoning validity', 'model inference', 'answer correctness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def declared_step_budget(rows, budget=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(budget) is not int or not 0 <= budget <= 10:
        raise ValueError('budget must be a nonbool integer between 0 and 10')
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
    values=sorted((n,min(y,budget),y-min(y,budget)) for n,x,y in clean)
    return {'progress':[(n,x+a) for (n,x,y),(m,a,b) in zip(sorted(clean),values)],
            'pending':[(n,b) for n,a,b in values],'complete':[n for n,a,b in values if b==0],
            'executed_count':sum(a for n,a,b in values)}
