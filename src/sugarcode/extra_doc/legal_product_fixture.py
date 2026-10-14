"""Row 1224, Legal Risk Assessment.

legal_product_fixture multiplies supplied abstract factors x and y. Returns
products in label order, over labels strictly above ceiling, maximum and
zero labels. No probabilities, exposure, liability or legal risk is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
ceiling defaults to 20, an exact int from 0 to 100.
Validation order: rows type, rows size, ceiling, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: legal risk assessment, probability estimation, legal advice, liability analysis, production readiness.
"""

SCOPE = 'PARTIAL: multiplies supplied abstract factor counts, no legal risk assessment'
NOT_CLAIMED = ('legal risk assessment', 'probability estimation', 'legal advice', 'liability analysis', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def legal_product_fixture(rows, ceiling=20):
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
    products=[(n,x*y) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'products':products,'over':[n for n,v in products if v>ceiling],
            'maximum':max(v for n,v in products),'zero':[n for n,v in products if v==0]}
