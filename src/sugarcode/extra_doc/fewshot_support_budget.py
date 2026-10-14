"""Row 1968, Few-Shot Learning.

fewshot_support_budget caps two supplied class-support counts x and y
independently at shots. Returns sorted chosen triples (label,class_a,
class_b), shortages label/count pairs counting missing support to reach
shots in both classes, balanced labels with equal chosen counts and total
chosen count. No examples are selected or evaluated. No few-shot learning,
model inference, example relevance or task performance is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
shots defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, shots, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: few-shot learning, model inference, example relevance, task performance, production readiness.
"""

SCOPE = 'PARTIAL: supplied class-support counts and shot cap, no few-shot learning'
NOT_CLAIMED = ('few-shot learning', 'model inference', 'example relevance', 'task performance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def fewshot_support_budget(rows, shots=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(shots) is not int or not 0 <= shots <= 10:
        raise ValueError('shots must be a nonbool integer between 0 and 10')
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
    chosen=sorted((n,min(x,shots),min(y,shots)) for n,x,y in clean)
    return {'chosen':chosen,'shortages':sorted((n,max(0,shots-x)+max(0,shots-y)) for n,x,y in clean),
            'balanced':[n for n,a,b in chosen if a==b],'total':sum(a+b for n,a,b in chosen)}
