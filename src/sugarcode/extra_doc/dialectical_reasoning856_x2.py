"""Row856 Dialectical Reasoning - Resolves contradictions.
Supplied thesis/antithesis integer delta ledger only. Rows(label,thesis-100..100,
antithesis-100..100),1..32. Report exact midpoint Fraction and disagreement
magnitude; flag opposite nonzero signs. Midpoint is not a justified synthesis.
NOT_CLAIMED: actual contradiction resolution, valid synthesis, argument truth,
philosophical reasoning, consensus or external effects.
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


def declared_opposed_values(rows):
    _rows(rows,'positions',32,3)
    for label,thesis,antithesis in rows:_label(label);_integer(thesis,-100,100);_integer(antithesis,-100,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('position labels must be unique')
    from fractions import Fraction
    return {'midpoints':[(l,Fraction(a+b,2),abs(a-b)) for l,a,b in sorted(rows,key=lambda r:r[0])],
            'opposed':[l for l,a,b in sorted(rows,key=lambda r:r[0]) if a*b<0],'synthesis_verified':False}
