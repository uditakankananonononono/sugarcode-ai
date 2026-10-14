"""Row 1970, In-Context Learning.

context_example_budget allocates an abstract count window to query y
first, then example x counts. Returns sorted allocations triples
(label,query_kept,examples_kept), dropped label/count pairs, query_truncated
strict labels and window. Counts are supplied lengths, not actual tokens.
No in-context learning, tokenization, model inference, example relevance
or real context construction is claimed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
window defaults to 8, an exact int from 0 to 10.
Validation order: rows type, rows size, window, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: in-context learning, tokenization, model inference, example relevance, production readiness.
"""

SCOPE = 'PARTIAL: supplied example/query count window allocation, no in-context learning'
NOT_CLAIMED = ('in-context learning', 'tokenization', 'model inference', 'example relevance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def context_example_budget(rows, window=8):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(window) is not int or not 0 <= window <= 10:
        raise ValueError('window must be a nonbool integer between 0 and 10')
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
    allocations=sorted((n,min(y,window),min(x,max(0,window-y))) for n,x,y in clean)
    return {'allocations':allocations,'dropped':sorted((n,x+y-a-b) for (n,x,y),(m,a,b) in zip(sorted(clean),allocations)),
            'query_truncated':sorted(n for n,x,y in clean if y>window),'window':window}
