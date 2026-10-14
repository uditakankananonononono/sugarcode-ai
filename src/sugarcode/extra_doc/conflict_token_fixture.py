"""Row 1299, Conflicts of Interest.

conflict_token_fixture counts abstract prefix overlap using the minimum of
supplied lengths x/y. Returns sorted overlaps, above labels strictly beyond
threshold, zero labels and total. No relationship, interest, actual conflict,
ethical rule or legal disclosure obligation is verified or inferred.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
threshold defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: conflict-of-interest judgment, relationships verification, legal ethics, disclosure obligations, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract paired prefix token overlap, no conflict-of-interest judgment'
NOT_CLAIMED = ('conflict-of-interest judgment', 'relationships verification', 'legal ethics', 'disclosure obligations', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def conflict_token_fixture(rows, threshold=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 0 <= threshold <= 10:
        raise ValueError('threshold must be a nonbool integer between 0 and 10')
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
    overlaps=[(n,min(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'overlaps':overlaps,'above':[n for n,v in overlaps if v>threshold],
            'zero':[n for n,v in overlaps if v==0],'total':sum(v for n,v in overlaps)}
