"""Row 1969, Zero-Shot Learning.

zeroshot_label_margin subtracts supplied rival y count from candidate
x count, accepts margins at least margin, and reports ties. Returns sorted
margins, accepted and ties label lists and best signed margin. Candidate
and rival counts are supplied arbitrary scores, not learned similarities.
No zero-shot learning, semantic similarity, model inference, label
correctness or evaluation execution is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
margin defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, margin, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: zero-shot learning, semantic similarity, model inference, label correctness, production readiness.
"""

SCOPE = 'PARTIAL: supplied candidate/rival count margin rule, no zero-shot learning'
NOT_CLAIMED = ('zero-shot learning', 'semantic similarity', 'model inference', 'label correctness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def zeroshot_label_margin(rows, margin=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(margin) is not int or not 0 <= margin <= 10:
        raise ValueError('margin must be a nonbool integer between 0 and 10')
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
    values=sorted((n,x-y) for n,x,y in clean)
    return {'margins':values,'accepted':[n for n,v in values if v>=margin],
            'ties':[n for n,v in values if v==0],'best':max(v for n,v in values)}
