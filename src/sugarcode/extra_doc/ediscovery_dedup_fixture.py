"""Row 1306, E-Discovery.

ediscovery_dedup_fixture subtracts abstract duplicate count y from total x,
floors at zero and caps at cap. Returns sorted retained, capped labels, total
and zero labels. No documents are read/retrieved/deduplicated, legal relevance
or privilege assessed, or preservation obligation fulfilled.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cap defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, cap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: e-discovery, document retrieval, privilege or relevance, legal preservation, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied dedup count tokens, no e-discovery'
NOT_CLAIMED = ('e-discovery', 'document retrieval', 'privilege or relevance', 'legal preservation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ediscovery_dedup_fixture(rows, cap=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cap) is not int or not 0 <= cap <= 10:
        raise ValueError('cap must be a nonbool integer between 0 and 10')
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
    retained=[(n,min(cap,max(0,x-y))) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'retained':retained,'capped':[n for n,v in retained if v==cap],
            'total':sum(v for n,v in retained),'zero':[n for n,v in retained if v==0]}
