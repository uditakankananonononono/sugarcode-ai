"""Row 1242, Employment Contracts.

employment_terms_fixture aligns the minimum of x, y and cap abstract terms from supplied
pairs. Returns sorted aligned counts, remaining unmatched total x+y-2*aligned
and capped labels attaining cap. No employment term, rights, duties or binding
contract is written or assessed.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
cap defaults to 5, an exact int from 0 to 10.
Validation order: rows type, rows size, cap, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: employment contracts, legal terms, enforceability, rights or duties, production readiness.
"""

SCOPE = 'PARTIAL: aligns supplied abstract term counts, no employment contract'
NOT_CLAIMED = ('employment contracts', 'legal terms', 'enforceability', 'rights or duties', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def employment_terms_fixture(rows, cap=5):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(cap) is not int or not 0 <= cap <= 10:
        raise ValueError('cap must be a nonbool integer between 0 and 10')
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
    aligned=[(n,min(x,y,cap)) for n,x,y in sorted(clean,key=lambda r:r[0])]
    return {'aligned':aligned,'remaining':[(n,x+y-2*v) for (n,x,y),(m,v) in zip(sorted(clean,key=lambda r:r[0]),aligned)],
            'capped':[n for n,v in aligned if v==cap]}
