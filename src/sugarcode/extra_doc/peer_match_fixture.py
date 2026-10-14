"""Row 1474, Peer Recommendation.

peer_match_fixture requires supplied skill count x meeting required and
availability count y positive, then ranks candidates by availability
descending and label ascending. Returns candidates (label,capped_skill,
availability), excluded sorted and best label or None. No real peer
recommendation, relationship inference, skill validation or learner needs
inference is supplied; no contact or disclosure is performed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
required defaults to 4, an exact int from 0 to 10.
Validation order: rows type, rows size, required, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: peer recommendation, relationship inference, learner needs inference, production readiness.
"""

SCOPE = 'PARTIAL: supplied skill/availability count matching, no peer recommendation'
NOT_CLAIMED = ('peer recommendation', 'relationship inference', 'learner needs inference', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def peer_match_fixture(rows, required=4):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(required) is not int or not 0 <= required <= 10:
        raise ValueError('required must be a nonbool integer between 0 and 10')
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
    values=sorted((n,min(x,required),y) for n,x,y in clean if x>=required and y>0)
    values.sort(key=lambda r:(-r[2],r[0]))
    return {'candidates':values,'excluded':sorted(n for n,x,y in clean if x<required or y==0),
            'best':values[0][0] if values else None}
