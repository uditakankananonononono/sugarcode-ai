"""Row504 Investor Relations - Manages relationships.
Supplied-data helper only. Rows (label, investor 0..15, day 0..365). Today is the latest day seen; gap is today minus an investor last contact day; stale means gap above 90.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: investor relationships, communication quality or external effects.
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


def analyze_investor_staleness(rows):
    _rows(rows, 'contacts', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 15)
        _integer(row[2], 0, 365)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('contact labels must be unique')
    last={}
    for row in rows:
        last[row[1]]=max(last.get(row[1],-1),row[2])
    today=max(row[2] for row in rows)
    out=[(investor,day,today-day) for investor,day in sorted(last.items(),key=lambda item:item[0])]
    return {'contacts':out,'stale':[investor for investor,_,gap in out if gap>90],'relationships_managed':False}
