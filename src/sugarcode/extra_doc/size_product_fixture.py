"""Row 1414, Size.

size_product_fixture multiplies supplied abstract share count x by price
count y and partitions at ceiling. Returns sorted products, small at most
ceiling including zero, large above and total. No actual market
capitalization, financial size classification, security selection, market
data lookup or financial advice is supplied.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
ceiling defaults to 20, an exact int from 0 to 100.
Validation order: rows type, rows size, ceiling, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: financial size classification, market capitalization, security selection, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: supplied share/price count product bands, no financial size classification'
NOT_CLAIMED = ('financial size classification', 'market capitalization', 'security selection', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def size_product_fixture(rows, ceiling=20):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(ceiling) is not int or not 0 <= ceiling <= 100:
        raise ValueError('ceiling must be a nonbool integer between 0 and 100')
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
    values=sorted((n,x*y) for n,x,y in clean)
    return {'products':values,'small':[n for n,v in values if v<=ceiling],
            'large':[n for n,v in values if v>ceiling],'total':sum(v for n,v in values)}
