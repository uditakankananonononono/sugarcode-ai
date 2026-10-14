"""Row 1965, Pre-trained Models.

pretrained_layer_freeze summarizes supplied frozen x and trainable y
layer counts. Returns sorted layers label/total pairs, within_budget
labels whose trainable count is at most budget, fully_frozen labels with
positive frozen and zero trainable counts, and trainable_total. An empty
model is not fully frozen. No pre-trained model, model loading, weight
validity, training behavior or parameter count is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
budget defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, budget, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: pre-trained model, model loading, weight validity, training behavior, production readiness.
"""

SCOPE = 'PARTIAL: supplied frozen/trainable layer count budget, no pre-trained model'
NOT_CLAIMED = ('pre-trained model', 'model loading', 'weight validity', 'training behavior', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def pretrained_layer_freeze(rows, budget=5):
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
    totals=sorted((n,x+y) for n,x,y in clean)
    return {'layers':totals,'within_budget':sorted(n for n,x,y in clean if y<=budget),
            'fully_frozen':sorted(n for n,x,y in clean if x>0 and y==0),
            'trainable_total':sum(y for n,x,y in clean)}
