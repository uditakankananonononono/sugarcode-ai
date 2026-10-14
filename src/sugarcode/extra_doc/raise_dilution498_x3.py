"""Row498 Fundraising Strategy - Plans capital raising.
Supplied-data helper only. Rows (label, round 0..31, raise 0..1000000, pre-money 1..10000000), unique rounds. Dilution per round is raise/(pre+raise); retained share is the exact product of (1-dilution).
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a real raise, investor interest or external effects.
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


def analyze_raise_dilution(rows):
    _rows(rows, 'rounds', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 31)
        _integer(row[2], 0, 1000000)
        _integer(row[3], 1, 10000000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('round labels must be unique')
    if len({row[1] for row in rows}) != len(rows):
        raise ValueError('round numbers must be unique')
    kept=Fraction(1)
    out=[]
    for row in sorted(rows,key=lambda r:r[1]):
        dilution=Fraction(row[2],row[3]+row[2])
        out.append((row[1],dilution))
        kept*=1-dilution
    return {'rounds':out,'retained':kept,'raise_planned':False}
