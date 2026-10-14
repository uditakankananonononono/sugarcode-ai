"""Row503 Term Sheet Negotiation - Structures deals.
Supplied-data helper only. Rows (label, term 0..7, side 0 ask/1 bid, value 0..1000). Per term the binding ask is the maximum ask and the binding bid the minimum bid; a term agrees when ask is at most bid. Terms with only one side are unpaired.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a deal, legal terms or external effects.
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


def analyze_term_overlap(rows):
    _rows(rows, 'positions', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 7)
        _integer(row[2], 0, 1)
        _integer(row[3], 0, 1000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('position labels must be unique')
    asks={}
    bids={}
    for row in rows:
        (asks if row[2]==0 else bids).setdefault(row[1],[]).append(row[3])
    agreed=[]
    conflict=[]
    unpaired=[]
    for term in sorted(set(asks)|set(bids)):
        if term not in asks or term not in bids:
            unpaired.append(term)
            continue
        low=max(asks[term])
        high=min(bids[term])
        if low<=high:
            agreed.append((term,low,high))
        else:
            conflict.append(term)
    return {'agreed':agreed,'conflict':conflict,'unpaired':unpaired,'deal_reached':False}
