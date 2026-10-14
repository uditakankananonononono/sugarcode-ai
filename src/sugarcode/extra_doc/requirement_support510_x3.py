"""Row510 Requirements Gathering - Elicits system needs.
Supplied-data helper only. Rows (label, stakeholder 0..15, requirement 0..31). Count distinct stakeholders per requirement; consensus means at least two.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: confirmed needs, stakeholders or external effects.
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


def analyze_requirement_support(rows):
    _rows(rows, 'requests', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 15)
        _integer(row[2], 0, 31)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('request labels must be unique')
    who={}
    for row in rows:
        who.setdefault(row[2],set()).add(row[1])
    counts=[(requirement,len(people)) for requirement,people in sorted(who.items(),key=lambda item:item[0])]
    return {'requirements':counts,'consensus':[requirement for requirement,count in counts if count>=2],'needs_confirmed':False}
