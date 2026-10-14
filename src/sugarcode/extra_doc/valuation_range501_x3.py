"""Row501 Valuation Analysis - Estimates worth.
Supplied-data helper only. Rows (label, metric 0..1000000, multiple in hundredths 0..10000). Value is metric*multiple/100 exactly; return per-label values, low, high and exact median.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a real valuation, market price or external effects.
"""
from fractions import Fraction


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


def analyze_valuation_range(rows):
    _rows(rows, 'estimates', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 1000000)
        _integer(row[2], 0, 10000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('estimate labels must be unique')
    values=sorted(Fraction(row[1]*row[2],100) for row in rows)
    count=len(values)
    middle=values[count//2] if count%2 else (values[count//2-1]+values[count//2])/2
    return {'values':[(row[0],Fraction(row[1]*row[2],100)) for row in sorted(rows,key=lambda r:r[0])],'low':values[0],'high':values[-1],'median':middle,'worth_estimated':False}
