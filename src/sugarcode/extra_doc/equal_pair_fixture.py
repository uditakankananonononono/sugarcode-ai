"""Row 1273, Equal Protection.

equal_pair_fixture inventories absolute difference and sum of abstract
paired counts. Returns sorted pairs (label,difference,total), within labels
at most tolerance, exact zero-difference labels and total_difference. No
people, protected classes, fairness, discrimination or legal rule is evaluated.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
tolerance defaults to 2, an exact int from 0 to 10.
Validation order: rows type, rows size, tolerance, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: equal protection, protected classes, discrimination or fairness, legal advice, production readiness.
"""

SCOPE = 'PARTIAL: compares abstract supplied pair parity, no equal protection finding'
NOT_CLAIMED = ('equal protection', 'protected classes', 'discrimination or fairness', 'legal advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def equal_pair_fixture(rows, tolerance=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(tolerance) is not int or not 0 <= tolerance <= 10:
        raise ValueError('tolerance must be a nonbool integer between 0 and 10')
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
    pairs=[(n,abs(x-y),x+y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'pairs':pairs,'within':[n for n,d,total in pairs if d<=tolerance],
            'exact':[n for n,d,total in pairs if d==0],'total_difference':sum(d for n,d,total in pairs)}
