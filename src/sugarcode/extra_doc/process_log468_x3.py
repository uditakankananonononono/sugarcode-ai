"""Row468 Process Mining - Discovers actual processes.
Supplied-data helper only. Rows (label, case 0..15, activity 0..15) in time order. Return sorted counts of directly-follows activity pairs within each case.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a real process model, conformance, log quality or external effects.
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


def analyze_process_log(rows):
    _rows(rows, 'events', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 15)
        _integer(row[2], 0, 15)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('event labels must be unique')
    last={}
    counts={}
    for row in rows:
        if row[1] in last:
            pair=(last[row[1]],row[2])
            counts[pair]=counts.get(pair,0)+1
        last[row[1]]=row[2]
    return {'follows':sorted(counts.items(),key=lambda item:item[0]),'process_discovered':False}
