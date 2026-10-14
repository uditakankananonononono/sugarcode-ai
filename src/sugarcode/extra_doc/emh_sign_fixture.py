"""Row 1410, EMH Testing.

emh_sign_fixture counts same-sign concordance for supplied signed count
pairs x and y, excluding either zero. Returns concordant, discordant and
excluded sorted labels, eligible count and meets for inclusive threshold
percentage of concordant or None if no eligible pairs. No real EMH test,
statistical significance, efficiency conclusion or financial advice is given.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
-10 to 10; bool and all subclasses are refused.
threshold defaults to 60, an exact int from 0 to 100.
Validation order: rows type, rows size, threshold, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: EMH test, statistical significance, market efficiency conclusion, financial advice, production readiness.
"""

SCOPE = 'PARTIAL: counts supplied pairwise directional concordance, no EMH test'
NOT_CLAIMED = ('EMH test', 'statistical significance', 'market efficiency conclusion', 'financial advice', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def emh_sign_fixture(rows, threshold=60):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(threshold) is not int or not 0 <= threshold <= 100:
        raise ValueError('threshold must be a nonbool integer between 0 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not -10 <= x <= 10:
            raise ValueError('x must be a nonbool integer between -10 and 10')
        if type(y) is not int or not -10 <= y <= 10:
            raise ValueError('y must be a nonbool integer between -10 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    eligible=[(n,x,y) for n,x,y in clean if x!=0 and y!=0]
    concordant=sorted(n for n,x,y in eligible if x*y>0)
    discordant=sorted(n for n,x,y in eligible if x*y<0)
    return {'concordant':concordant,'discordant':discordant,'excluded':sorted(n for n,x,y in clean if x==0 or y==0),
            'meets':100*len(concordant)>=threshold*len(eligible) if eligible else None,'eligible':len(eligible)}
