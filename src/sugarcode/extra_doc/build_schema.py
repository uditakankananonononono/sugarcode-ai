"""Row 879, Schema Development - Builds frameworks.

build_schema takes two integer observations per named field. The permitted
range spans both observations, expanded by padding and clipped to [0,100].
Returns fields as (label, inclusive_low, inclusive_high) in label order,
cardinalities as each field's number of permitted integer values, fixed as
sorted labels whose final permitted range has only one value. Observations
may arrive in either order; no persisted schema or validation is created.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
padding defaults to 1, an exact int from 0 to 5.
Validation order: rows type, rows size, padding, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: schema inference, type inference, future data validity, database enforcement, production readiness.
"""

SCOPE = 'PARTIAL: derives bounded integer field ranges from two supplied observations, no schema is learned'
NOT_CLAIMED = ('schema inference', 'type inference', 'future data validity', 'database enforcement', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def build_schema(rows, padding=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(padding) is not int or not 0 <= padding <= 5:
        raise ValueError('padding must be a nonbool integer between 0 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    fields = []
    for label, x, y in sorted(clean, key=lambda r: r[0]):
        low = max(0, min(x, y) - padding)
        high = min(100, max(x, y) + padding)
        fields.append((label, low, high))
    return {'fields': fields, 'cardinalities': {n: high - low + 1 for n, low, high in fields},
            'fixed': [n for n, low, high in fields if low == high]}
