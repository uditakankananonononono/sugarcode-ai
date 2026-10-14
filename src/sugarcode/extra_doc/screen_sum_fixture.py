"""Row 1145, Depression Screening.

screen_sum_fixture adds supplied integer item pairs x+y and compares their
aggregate with caller cutoff. Returns items as sorted (label,pair_sum), total
as sum of all item sums, above as total>=cutoff, distance as total-cutoff.
No depression instrument, diagnostic category or clinical threshold is used;
this is abstract score bookkeeping only.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cutoff defaults to 10, an exact int from 0 to 100.
Validation order: rows type, rows size, cutoff, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: depression screening, clinical instrument, diagnosis, item validity, production readiness.
"""

SCOPE = 'PARTIAL: counts supplied paired item scores against an abstract aggregate cutoff, no depression is screened'
NOT_CLAIMED = ('depression screening', 'clinical instrument', 'diagnosis', 'item validity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def screen_sum_fixture(rows, cutoff=10):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cutoff) is not int or not 0 <= cutoff <= 100:
        raise ValueError('cutoff must be a nonbool integer between 0 and 100')
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
    items = [(n, first + second) for n, first, second in sorted(clean, key=lambda r: r[0])]
    total = sum(v for n, v in items)
    above = total >= cutoff
    return {'items': items, 'total': total, 'above': above,
            'distance': total - cutoff}
