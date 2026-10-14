"""Row844 Spatial Reasoning - Reasons about space.
Supplied 2D lattice point pair arithmetic only. Rows(label,x1,y1,x2,y2),1..32;
coordinates exact integers-1000..1000. Return Manhattan and squared Euclidean
distances, sorted by label. No real location or geometric interpretation.
NOT_CLAIMED: spatial intelligence, actual distances, map interpretation,
physical navigation, dimensional validity or external effects.
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


def lattice_point_distances(rows):
    _rows(rows,'points',32,5)
    for label,x1,y1,x2,y2 in rows:
        _label(label)
        for coordinate in (x1,y1,x2,y2):_integer(coordinate,-1000,1000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('point labels must be unique')
    return {'distances':[(label,abs(x2-x1)+abs(y2-y1),(x2-x1)**2+(y2-y1)**2) for label,x1,y1,x2,y2 in sorted(rows)],'locations_verified':False}
