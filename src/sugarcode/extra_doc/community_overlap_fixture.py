"""Row 1207, Community Health Assessment.

community_overlap_fixture normalizes supplied endpoints into closed
integer windows. Returns windows sorted by label, active labels containing
point and overlaps (first_label,second_label,shared_integer_count) for
intersecting pairs in lexical label order. No community health is measured.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
point defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, point, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: community health assessment, population measurement, clinical needs, causal interpretation, production readiness.
"""

SCOPE = 'PARTIAL: counts overlap of abstract supplied integer windows, no community health assessment'
NOT_CLAIMED = ('community health assessment', 'population measurement', 'clinical needs', 'causal interpretation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def community_overlap_fixture(rows, point=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(point) is not int or not 0 <= point <= 10:
        raise ValueError('point must be a nonbool integer between 0 and 10')
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
    windows=[(n,min(x,y),max(x,y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    active=[n for n,a,b in windows if a<=point<=b]
    overlaps=[]
    for i,(n,a,b) in enumerate(windows):
        for m,c,d in windows[i+1:]:
            size=max(0,min(b,d)-max(a,c)+1)
            if size: overlaps.append((n,m,size))
    return {'active':active,'overlaps':overlaps,'windows':windows}
