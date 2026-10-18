"""Bounded exact integer-weight counting on caller-supplied item sequences.

SCOPE: up to eight indexed items, positive weights<=32, target<=32.
NOT_CLAIMED: purchases, allocation policy, large-scale optimization, integration.
"""
CLAIMS = False
SCOPE = "finite exact indexed-item weight counts and bounded knapsack values"
NOT_CLAIMED = "purchases, allocation policy, large-scale optimization, product integration"
MAX_ITEMS=8
MAX_TARGET=32
MAX_COUNT=8
MAX_VALUE=100


def _int(x,name,low,high):
    if isinstance(x,bool):raise TypeError(name+" must be an integer")
    if not isinstance(x,int):raise TypeError(name+" must be an integer")
    if x<low or x>high:raise ValueError(name+" out of range")
    return x


def _weights(weights,target):
    if not isinstance(weights,(list,tuple)):raise TypeError("weights must be a list or tuple")
    if len(weights)>MAX_ITEMS:raise ValueError("item count out of range")
    _int(target,'target',0,MAX_TARGET)
    return tuple(_int(x,'weight',1,MAX_TARGET) for x in weights)


def _hist(weights,target,counts):
    ways=[0]*(target+1);ways[0]=1
    for weight,count in zip(weights,counts):
        updated=[0]*(target+1)
        for total,number in enumerate(ways):
            for k in range(min(count,(target-total)//weight)+1):updated[total+k*weight]+=number
        ways=updated
    return tuple(ways)


def _bounded(weights,target,counts):
    ws=_weights(weights,target)
    if not isinstance(counts,(list,tuple)):raise TypeError("counts must be a list or tuple")
    if len(counts)!=len(ws):raise ValueError("counts size mismatch")
    cs=tuple(_int(x,'count',0,MAX_COUNT) for x in counts)
    return ws,cs


def subset_sum_count(weights,target):
    ws=_weights(weights,target)
    return _hist(ws,target,[1]*len(ws))[-1]


def subset_sum_histogram(weights,target):
    ws=_weights(weights,target)
    return _hist(ws,target,[1]*len(ws))


def bounded_sum_count(weights,target,counts):
    ws,cs=_bounded(weights,target,counts)
    return _hist(ws,target,cs)[-1]


def bounded_sum_histogram(weights,target,counts):
    ws,cs=_bounded(weights,target,counts)
    return _hist(ws,target,cs)


def unbounded_sum_count(weights,target):
    """Equal weights at different indices remain distinct item types."""
    ws=_weights(weights,target)
    ways=[0]*(target+1);ways[0]=1
    for weight in ws:
        for total in range(weight,target+1):ways[total]+=ways[total-weight]
    return ways[-1]


def minimum_coin_count(weights,target):
    ws=_weights(weights,target)
    best=[target+1]*(target+1);best[0]=0
    for total in range(1,target+1):
        best[total]=min((best[total-w]+1 for w in ws if w<=total),default=target+1)
    return best[-1] if best[-1]<=target else None


def exact_cardinality_count(weights,target,cardinality):
    ws=_weights(weights,target)
    _int(cardinality,'cardinality',0,MAX_ITEMS)
    ways=[[0]*(cardinality+1) for _ in range(target+1)];ways[0][0]=1
    for weight in ws:
        for total in range(target,weight-1,-1):
            for k in range(cardinality,0,-1):ways[total][k]+=ways[total-weight][k-1]
    return ways[target][cardinality]


def _knapsack(weights,target,values):
    ws=_weights(weights,target)
    if not isinstance(values,(list,tuple)):raise TypeError("values must be a list or tuple")
    if len(values)!=len(ws):raise ValueError("values size mismatch")
    vs=tuple(_int(x,'value',-MAX_VALUE,MAX_VALUE) for x in values)
    states={0:(0,1)}
    for weight,value in zip(ws,vs):
        updated=dict(states)
        for total,(score,count) in states.items():
            new=total+weight
            if new<=target:
                candidate=score+value
                if new not in updated or candidate>updated[new][0]:updated[new]=(candidate,count)
                elif candidate==updated[new][0]:updated[new]=(candidate,updated[new][1]+count)
        states=updated
    optimum=max(score for score,count in states.values())
    return optimum,sum(count for score,count in states.values() if score==optimum)


def knapsack_max_value(weights,target,values):
    return _knapsack(weights,target,values)[0]


def optimal_knapsack_count(weights,target,values):
    return _knapsack(weights,target,values)[1]


def feasible_subset_count(weights,target):
    ws=_weights(weights,target)
    return sum(_hist(ws,target,[1]*len(ws)))
