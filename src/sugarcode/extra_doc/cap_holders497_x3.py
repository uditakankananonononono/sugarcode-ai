"""Row497 Cap Table Management - Tracks ownership.
Supplied-data helper only. Rows (label, holder 0..15, class 0..2, shares 0..1000000). Return shares and exact ownership fraction per holder, total shares and sorted classes seen.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: legal ownership, a valid cap table or external effects.
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


def analyze_cap_holders(rows):
    _rows(rows, 'grants', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 15)
        _integer(row[2], 0, 2)
        _integer(row[3], 0, 1000000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('grant labels must be unique')
    held={}
    for row in rows:
        held[row[1]]=held.get(row[1],0)+row[3]
    total=sum(held.values())
    out=[(holder,shares,Fraction(shares,total) if total else Fraction(0)) for holder,shares in sorted(held.items(),key=lambda item:item[0])]
    return {'holders':out,'total_shares':total,'classes':sorted({row[2] for row in rows}),'cap_table_verified':False}
