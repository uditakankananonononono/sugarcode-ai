"""Row 1287, Depositions.

deposition_turn_fixture compares abstract questions x plus reserve with
answer count y and floors unresolved at zero. Returns sorted unresolved,
complete zero labels, extra labels above count requirement and total. No
actual testimony, truth, credibility, deposition or legal process is assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
reserve defaults to 1, an exact int from 0 to 10.
Validation order: rows type, rows size, reserve, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: deposition analysis, testimony truth, credibility, legal procedure, production readiness.
"""

SCOPE = 'PARTIAL: inventories abstract supplied question/answer tallies, no deposition analysis'
NOT_CLAIMED = ('deposition analysis', 'testimony truth', 'credibility', 'legal procedure', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def deposition_turn_fixture(rows, reserve=1):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(reserve) is not int or not 0 <= reserve <= 10:
        raise ValueError('reserve must be a nonbool integer between 0 and 10')
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
    unresolved=[(n,max(0,x+reserve-y)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'unresolved':unresolved,'complete':[n for n,v in unresolved if v==0],
            'extra':sorted(n for n,x,y in clean if y>x+reserve),'total':sum(v for n,v in unresolved)}
