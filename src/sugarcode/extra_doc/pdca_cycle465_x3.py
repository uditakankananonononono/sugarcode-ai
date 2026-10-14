"""Row465 PDCA Cycle - Plan-Do-Check-Act.
Supplied-data helper only. Rows (label, phase 0..3 = plan/do/check/act, units 0..1000). Return phase totals, completed cycles as the minimum total, and the lowest phase index holding that minimum.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: improvement, quality, a real cycle having run or external effects.
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


def analyze_pdca_cycle(rows):
    _rows(rows, 'entries', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 3)
        _integer(row[2], 0, 1000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('entry labels must be unique')
    totals=[0,0,0,0]
    for row in rows:
        totals[row[1]]+=row[2]
    low=min(totals)
    return {'totals':totals,'cycles':low,'next_phase':totals.index(low),'cycle_verified':False}
