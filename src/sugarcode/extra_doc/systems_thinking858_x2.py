"""Row858 Systems Thinking - Sees wholes.
Supplied finite directed weighted flow ledger only. Rows(label,source0..15,
target0..15,amount0..1000),1..32. Return every mentioned node's inbound,
outbound and net inbound-minus-outbound totals sorted by node. Selfloops allowed.
NOT_CLAIMED: actual system understanding, valid flows, causal structure,
feedback predictions, system optimization or external effects.
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


def declared_flow_balances(rows):
    _rows(rows,'flows',32,4)
    for label,source,target,amount in rows:_label(label);_integer(source,0,15);_integer(target,0,15);_integer(amount,0,1000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('flow labels must be unique')
    nodes=sorted({s for _,s,_,_ in rows}|{t for _,_,t,_ in rows});balances=[]
    for node in nodes:
        incoming=sum(a for _,_,t,a in rows if t==node);outgoing=sum(a for _,s,_,a in rows if s==node)
        balances.append((node,incoming,outgoing,incoming-outgoing))
    return {'balances':balances,'system_verified':False}
