"""Row506 Exit Planning - Prepares for liquidity.
Supplied-data helper only. Rows (label, year 0..10, proceeds 0..1000000, tax basis points 0..10000). Net is proceeds*(10000-tax)/10000 exactly; rank by net descending, then earlier year, then label.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: an executed exit, tax advice or external effects.
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


def analyze_exit_net(rows):
    _rows(rows, 'options', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 10)
        _integer(row[2], 0, 1000000)
        _integer(row[3], 0, 10000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('option labels must be unique')
    ranked=sorted(((row[0],Fraction(row[2]*(10000-row[3]),10000),row[1]) for row in rows),key=lambda item:(-item[1],item[2],item[0]))
    return {'ranked':[(label,net) for label,net,_ in ranked],'best':ranked[0][0],'exit_executed':False}
