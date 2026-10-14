"""Row 1201, Crisis Intervention.

abstract_escalation_fixture subtracts supplied abstract threshold y and
margin from count x. Returns excess ordered descending then label, above
positive labels, equal zero labels and maximum signed excess. These are
opaque count fixtures, not personal risk, clinical urgency or danger. No
crisis is assessed, response advised, person contacted or emergency acted on.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
margin defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, margin, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: crisis intervention, urgency or danger assessment, clinical safety, emergency response, production readiness.
"""

SCOPE = 'PARTIAL: ranks opaque supplied threshold excesses, no crisis intervention'
NOT_CLAIMED = ('crisis intervention', 'urgency or danger assessment', 'clinical safety', 'emergency response', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def abstract_escalation_fixture(rows, margin=1):
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
    excess=[(n,x-y-margin) for n,x,y in clean]
    excess.sort(key=lambda r:(-r[1],r[0]))
    return {'excess':excess,'above':[n for n,v in excess if v>0],
            'equal':[n for n,v in excess if v==0],'maximum':excess[0][1]}
