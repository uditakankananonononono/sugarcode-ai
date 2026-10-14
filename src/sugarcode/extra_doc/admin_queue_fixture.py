"""Row 1274, Administrative Law.

admin_queue_fixture orders abstract paired totals ascending then label and
numbers them from offset. Returns queue (label,index,total), next_index and
zero-total labels in queue order. No agency rule, docket, legal priority,
administrative procedure or deadline is interpreted.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
offset defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, offset, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: administrative law, agency rules, legal deadlines, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: orders abstract supplied administrative count tokens, no administrative law analysis'
NOT_CLAIMED = ('administrative law', 'agency rules', 'legal deadlines', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def admin_queue_fixture(rows, offset=2):
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
    ordered=sorted(clean,key=lambda r:(r[1]+r[2],r[0]))
    queue=[(n,offset+i,x+y) for i,(n,x,y) in enumerate(ordered)]
    return {'queue':queue,'next_index':offset+len(queue),'zero':[n for n,i,total in queue if total==0]}
