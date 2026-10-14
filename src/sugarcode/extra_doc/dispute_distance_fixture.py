"""Row 1284, Dispute Resolution.

dispute_distance_fixture computes Manhattan distance of abstract pair
positions to (target,target). Returns distances ascending then label, nearest
all minimum labels and exact zero labels. No actual party interests, consent,
settlement, dispute or legal outcome is assessed or negotiated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
target defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, target, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: dispute resolution, party consent, legal settlement, external negotiation, production readiness.
"""

SCOPE = 'PARTIAL: ranks abstract supplied position distances, no dispute resolution'
NOT_CLAIMED = ('dispute resolution', 'party consent', 'legal settlement', 'external negotiation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def dispute_distance_fixture(rows, target=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(target) is not int or not 0 <= target <= 10:
        raise ValueError('target must be a nonbool integer between 0 and 10')
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
    distances=[(n,abs(x-target)+abs(y-target)) for n,x,y in clean]
    distances.sort(key=lambda r:(r[1],r[0]))
    return {'distances':distances,'nearest':[n for n,v in distances if v==distances[0][1]],
            'exact':[n for n,v in distances if v==0]}
