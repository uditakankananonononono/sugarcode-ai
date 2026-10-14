"""Carbon Cycle Analysis.

PARTIAL: caller nonnegative pool-transfer ledger arithmetic only, not carbon
cycle analysis,flux estimates,chemical dynamics or climate projections.
Pool balances/transfers are caller abstractions,not measured carbon reservoirs.
"""
SCOPE='caller pool-transfer ledger only; no carbon flux or climate analysis claims'


def transfer(balances,moves):
    """Balances exactlist/tuple1..32(label,amount),unique printable Unicode
    exactstr1..40;amount exactint0..1000000. Moves exactlist/tuple0..64(from,to,
    amount),known distinct exactstr labels,amount same range. Sequential transfers
    may not overdraw current source. Return label-sorted final balances and total
    conserved amount. Mixedrows accepted;caller move order preserved. No external
    emissions,sequestration,units,real reservoirs or physical constraints inferred.
    """
    def text(x):
        if type(x) is not str or not 1<=len(x)<=40 or not all(ch.isprintable() for ch in x):raise ValueError('label must be exactstr printable Unicode length1..40')
    def amount(x):
        if type(x) is not int or not 0<=x<=1000000:raise ValueError('amount must be exactint0..1000000')
    if type(balances) not in (list,tuple) or not 1<=len(balances)<=32:raise ValueError('balances must be exactlist/tuple length1..32')
    pools={}
    for row in balances:
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('balance row must be exactlist/tuple pair')
        label,value=row;text(label)
        if label in pools:raise ValueError('pool labels must be unique')
        amount(value);pools[label]=value
    if type(moves) not in (list,tuple) or len(moves)>64:raise ValueError('moves must be exactlist/tuple atmost64')
    parsed=[]
    for row in moves:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('move row must be exactlist/tuple triple')
        source,target,value=row;text(source);text(target);amount(value)
        if source not in pools or target not in pools or source==target:raise ValueError('move endpoints must be distinct known pools')
        parsed.append((source,target,value))
    for source,target,value in parsed:
        if value>pools[source]:raise ValueError('move must not overdraw current source')
        pools[source]-=value;pools[target]+=value
    return {'balances':tuple(sorted(pools.items())),'total':sum(pools.values()),'scope':SCOPE}
