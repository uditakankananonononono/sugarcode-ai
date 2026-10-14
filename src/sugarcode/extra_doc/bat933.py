"""Bat Algorithm - Echolocation-inspired.

PARTIAL: double-precision one-generation bat frequency/velocity update with
caller-controlled pulse/local-search and acceptance draws on sphere objective.
No hardware, RNG, convergence or global optimum guarantee.
"""
from math import isfinite
SCOPE='one synchronous bat frequency velocity and acceptance generation on sphere'


def generation(rows,frequencies,pulse_draws,accept_draws,local_offsets,pulse_rate=.5,loudness=.5,bound=10.):
    """Rows(positionvector,velocityvector),1..16 bats,dim1..4,box[-bound,bound].

    old best is minimum sphere score, index ties. v'=v+(x-best)*frequency;
    candidate=clip(x+v'). If pulse_draw>pulse_rate use best+local_offset instead.
    Accept only strictly better candidate and accept_draw<loudness. Velocity
    updates regardless of acceptance; no adaptive loudness/pulse schedule.
    freq[0,2],draws[0,1],localoffset[-1,1],loudness/pulserate[0,1],bound(0,100].
    All candidates from old best, synchronous. Exactbuilt-in finite int/float.
    """
    def real(x,lo,hi):
        if type(x) not in (int,float) or not lo<=x<=hi or not isfinite(x):raise ValueError('finite built-in bat real outside range')
        return float(x)
    pr=real(pulse_rate,0,1);la=real(loudness,0,1);limit=real(bound,0,100)
    if limit==0:raise ValueError('bound must be positive')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=16:raise ValueError('rows must contain1..16 bats')
    if type(rows[0]) not in (list,tuple) or len(rows[0])!=2 or type(rows[0][0]) not in (list,tuple) or not 1<=len(rows[0][0])<=4:raise ValueError('bat rows require two equal1..4 dimensional vectors')
    dim=len(rows[0][0]);states=[]
    def vector(row,lo,hi):
        if type(row) not in (list,tuple) or len(row)!=dim:raise ValueError('bat rows require two equal1..4 dimensional vectors')
        return tuple(real(x,lo,hi) for x in row)
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('bat rows require two equal1..4 dimensional vectors')
        states.append((vector(row[0],-limit,limit),vector(row[1],-100,100)))
    n=len(states)
    for seq in (frequencies,pulse_draws,accept_draws,local_offsets):
        if type(seq) not in (list,tuple) or len(seq)!=n:raise ValueError('one frequency/draw/offset per bat required')
    fs=[real(x,0,2) for x in frequencies];ps=[real(x,0,1) for x in pulse_draws];ads=[real(x,0,1) for x in accept_draws];offsets=[vector(row,-1,1) for row in local_offsets]
    score=lambda row:sum(x*x for x in row);best_index=min(range(n),key=lambda i:(score(states[i][0]),i));best=states[best_index][0];output=[];accepted=[];local=[]
    for i,(x,v) in enumerate(states):
        velocity=tuple(vv+(xx-bb)*fs[i] for xx,vv,bb in zip(x,v,best))
        candidate=tuple(max(-limit,min(limit,xx+vv)) for xx,vv in zip(x,velocity))
        if ps[i]>pr:
            local.append(i);candidate=tuple(max(-limit,min(limit,bb+delta)) for bb,delta in zip(best,offsets[i]))
        if score(candidate)<score(x) and ads[i]<la:position=candidate;accepted.append(i)
        else:position=x
        output.append((position,velocity))
    return {'bats':tuple(output),'accepted':tuple(accepted),'local_search':tuple(local),'best_index_before':best_index,'scope':SCOPE}
