"""Row 1456, Mobile Learning.

mobile_download_fixture adds fixed overhead count to supplied asset size
x and divides by supplied bandwidth count y, rounding batches up; zero
bandwidth is undefined even for zero load. Returns sorted batches
(label,int or None), blocked, total defined batches and overhead. No mobile
learning delivery, real network measurement or device compatibility is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
overhead defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, overhead, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: mobile learning delivery, device compatibility, network measurement, production readiness.
"""

SCOPE = 'PARTIAL: supplied asset/bandwidth count download batches, no mobile learning delivery'
NOT_CLAIMED = ('mobile learning delivery', 'device compatibility', 'network measurement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def mobile_download_fixture(rows, overhead=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(overhead) is not int or not 0 <= overhead <= 5:
        raise ValueError('overhead must be a nonbool integer between 0 and 5')
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
    values=sorted((n,(x+overhead+y-1)//y if y else None) for n,x,y in clean)
    return {'batches':values,'blocked':[n for n,v in values if v is None],
            'total':sum(v for n,v in values if v is not None),'overhead':overhead}
