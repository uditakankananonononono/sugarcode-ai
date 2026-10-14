"""Row 1200, Harm Reduction.

supply_bundle_fixture subtracts abstract reserved y from stock x, floors at
zero, then counts full bundle units and leftover units. Returns sorted
supplies (label,full_bundles,remainder), total_bundles and no_bundle labels.
No supplies are identified, allocated, recommended or judged to reduce harm;
no clinical suitability, risk reduction or safety is implied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
bundle defaults to 3, an exact int from 1 to 10.
Validation order: rows type, rows size, bundle, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: harm reduction advice, risk or safety guarantee, clinical suitability, real resource allocation, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied bundle capacity, no harm reduction advice'
NOT_CLAIMED = ('harm reduction advice', 'risk or safety guarantee', 'clinical suitability', 'real resource allocation', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def supply_bundle_fixture(rows, bundle=3):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(bundle) is not int or not 1 <= bundle <= 10:
        raise ValueError('bundle must be a nonbool integer between 1 and 10')
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
    supplies=[]
    for n,stock,reserved in sorted(clean,key=lambda r:r[0]):
        free=max(0,stock-reserved)
        count,remainder=divmod(free,bundle)
        supplies.append((n,count,remainder))
    return {'supplies':supplies,'total_bundles':sum(c for n,c,r in supplies),
            'no_bundle':[n for n,c,r in supplies if c==0]}
