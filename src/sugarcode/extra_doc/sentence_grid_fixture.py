"""Row 1267, Sentencing Guidelines.

sentence_grid_fixture sums abstract paired counts and clips at cap. Returns
sorted grid, capped labels attaining cap and excess as nonnegative over-cap
counts. No crime, sentence, penalty, statutory grid or jurisdiction is modeled;
these numbers must not be interpreted as legal sentencing guidance.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cap defaults to 7, an exact int from 0 to 20.
Validation order: rows type, rows size, cap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: sentencing guidelines, criminal penalty, legal advice, jurisdictional law, production readiness.
"""

SCOPE = 'PARTIAL: maps supplied abstract grid counts, no sentencing guidelines'
NOT_CLAIMED = ('sentencing guidelines', 'criminal penalty', 'legal advice', 'jurisdictional law', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def sentence_grid_fixture(rows, cap=7):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cap) is not int or not 0 <= cap <= 20:
        raise ValueError('cap must be a nonbool integer between 0 and 20')
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
    grid=[(n,min(cap,x+y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'grid':grid,'capped':[n for n,v in grid if v==cap],
            'excess':[(n,max(0,x+y-cap)) for n,x,y in sorted(clean,key=lambda r:r[0])]}
