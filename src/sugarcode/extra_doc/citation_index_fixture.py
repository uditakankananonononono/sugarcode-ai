"""Row 1294, Legal Citations.

citation_index_fixture adds offset to abstract paired index tokens. Returns
sorted citations (label,first_index,second_index), same equal-index labels
and backward second-less-than-first labels. No authority is retrieved and no
citation syntax, legal style, source authenticity or legal validity is verified.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
offset defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, offset, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal citation validation, authority retrieval, Bluebook or local style, source authenticity, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied citation index tokens, no legal citation validation'
NOT_CLAIMED = ('legal citation validation', 'authority retrieval', 'Bluebook or local style', 'source authenticity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def citation_index_fixture(rows, offset=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(offset) is not int or not 0 <= offset <= 10:
        raise ValueError('offset must be a nonbool integer between 0 and 10')
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
    citations=[(n,offset+x,offset+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'citations':citations,'same':[n for n,a,b in citations if a==b],
            'backward':[n for n,a,b in citations if b<a]}
