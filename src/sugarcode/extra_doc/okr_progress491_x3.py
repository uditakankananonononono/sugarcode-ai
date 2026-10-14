"""Row491 OKR Setting - Defines objectives and key results.
Supplied-data helper only. Rows (label, objective 0..7, key-result progress 0..100). Return the exact mean progress per objective and objectives at or above 70.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: achieved objectives, good OKRs or external effects.
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


def analyze_okr_progress(rows):
    _rows(rows, 'results', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 7)
        _integer(row[2], 0, 100)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('result labels must be unique')
    groups={}
    for row in rows:
        groups.setdefault(row[1],[]).append(row[2])
    out=[(objective,Fraction(sum(values),len(values))) for objective,values in sorted(groups.items(),key=lambda item:item[0])]
    return {'objectives':out,'achieved':[objective for objective,mean in out if mean>=70],'okr_achieved':False}
