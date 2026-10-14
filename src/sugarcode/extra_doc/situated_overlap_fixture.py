"""Row 1439, Situated Learning.

situated_overlap_fixture treats supplied training x and application y
counts as prefix sets and counts their overlap and unmatched count. Returns
sorted overlaps (label,overlap,gap), meeting inclusive minimum overlap,
overlap_total and gap_total. No situated-learning assessment, context
validity, skill-transfer inference or educational recommendation is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
minimum defaults to 3, an exact int from 0 to 10.
Validation order: rows type, rows size, minimum, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: situated learning assessment, context validity, skill transfer inference, production readiness.
"""

SCOPE = 'PARTIAL: supplied paired context-count overlap, no situated-learning assessment'
NOT_CLAIMED = ('situated learning assessment', 'context validity', 'skill transfer inference', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def situated_overlap_fixture(rows, minimum=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(minimum) is not int or not 0 <= minimum <= 10:
        raise ValueError('minimum must be a nonbool integer between 0 and 10')
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
    values=sorted((n,min(x,y),abs(x-y)) for n,x,y in clean)
    return {'overlaps':values,'meeting':[n for n,v,g in values if v>=minimum],
            'overlap_total':sum(v for n,v,g in values),'gap_total':sum(g for n,v,g in values)}
