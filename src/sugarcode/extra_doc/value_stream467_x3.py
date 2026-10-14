"""Row467 Value Stream Mapping - Visualizes flow.
Supplied-data helper only. Rows (label, process 0..1000, wait 0..1000) in flow order. Return lead time, value-added time, exact efficiency Fraction (0 when lead is 0) and the first step with the largest process time.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: real flow, waste removal, a drawn map or external effects.
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


def analyze_value_stream(rows):
    _rows(rows, 'steps', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 1000)
        _integer(row[2], 0, 1000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('step labels must be unique')
    process=sum(row[1] for row in rows)
    lead=sum(row[1]+row[2] for row in rows)
    slow=0
    for index,row in enumerate(rows):
        if row[1]>rows[slow][1]:
            slow=index
    return {'lead_time':lead,'value_added':process,'efficiency':Fraction(process,lead) if lead else Fraction(0),'bottleneck':rows[slow][0],'flow_improved':False}
