"""Row470 Robotic Process Automation - Automates repetitive tasks.
Supplied-data helper only. Rows (label, runs per week 0..1000, minutes per run 0..600, error basis points 0..10000). Return per task weekly minutes and exact rework minutes, plus the exact total.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a deployed bot, actual run times, accuracy or external effects.
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


def analyze_rpa_rework(rows):
    _rows(rows, 'tasks', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 1000)
        _integer(row[2], 0, 600)
        _integer(row[3], 0, 10000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('task labels must be unique')
    out=[]
    total=Fraction(0)
    for label,runs,minutes,error in sorted(rows,key=lambda r:r[0]):
        weekly=runs*minutes
        rework=Fraction(weekly*error,10000)
        out.append((label,weekly,rework))
        total+=weekly+rework
    return {'tasks':out,'weekly_minutes_with_rework':total,'rpa_deployed':False}
