"""Row849 Fuzzy Logic - Handles vagueness.
Supplied membership-basispoint algebra only. Rows(label,A0..10000,B0..10000),
1..32. Return min t-norm,max t-conorm,complementA10000-A and
Lukasiewicz t-norm max(A+B-10000,0). No semantic membership verification.
NOT_CLAIMED: valid fuzzy sets, vague meaning interpretation, decisions,
real-world inference, calibrated membership or external effects.
"""
def _rows(value, name, cap, arity):
    if type(value) not in (list, tuple): raise TypeError(name + ': exact list or tuple required')
    if not 1 <= len(value) <= cap: raise ValueError(name + ': row count outside declared range')
    for row in value:
        if type(row) not in (list, tuple): raise TypeError(name + ': exact list or tuple row required')
        if len(row) != arity: raise ValueError(name + ': wrong row arity')


def _label(value):
    if type(value) is not str: raise TypeError('exact string label required')
    if not 1 <= len(value) <= 24 or not value.isascii() or not all(c.isalnum() or c == '_' for c in value):
        raise ValueError('label must be 1..24 ASCII word characters')


def _integer(value, lo, hi):
    if type(value) is not int: raise TypeError('exact nonbool integer required')
    if not lo <= value <= hi: raise ValueError('integer outside declared range')


def declared_membership_algebra(rows):
    _rows(rows,'memberships',32,3)
    for label,a,b in rows:_label(label);_integer(a,0,10000);_integer(b,0,10000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('membership labels must be unique')
    return {'memberships':[(label,min(a,b),max(a,b),10000-a,max(a+b-10000,0)) for label,a,b in sorted(rows)],'memberships_verified':False}
