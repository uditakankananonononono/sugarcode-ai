"""Row268 Pacing Control: exact constrained scene-duration generation.

Generate integer durations for supplied beat labels, per-scene bounds and target
rhythm curve, minimizing squared target error under exact total duration.
Certificate reports optimal objective and constraint satisfaction. Lexicographic
schedule breaks ties. NOT_CLAIMED reader-perceived rhythm, original narrative,
creative quality, learned pacing or full unconstrained story generation.
"""
from fractions import Fraction as F


def _integer(x,lo,hi):
    if type(x) is not int:raise TypeError('exact nonbool integer required')
    if not lo<=x<=hi:raise ValueError('integer cap or range exceeded')


def pacing_control(beats,targets,total):
    _integer(total,1,48)
    if not isinstance(beats,list) or not 1<=len(beats)<=6:raise ValueError('beat cap 1..6 required')
    if not isinstance(targets,list) or len(targets)!=len(beats):raise ValueError('one target per beat required')
    for row in beats:
        if type(row) is not tuple or len(row)!=3:raise ValueError('label/min/max beat required')
        label,lo,hi=row
        if type(label) is not str or not 1<=len(label)<=20:raise ValueError('bounded beat label required')
        _integer(lo,1,8);_integer(hi,1,8)
        if lo>hi:raise ValueError('min exceeds max')
    for target in targets:_integer(target,0,8)
    if not sum(row[1] for row in beats)<=total<=sum(row[2] for row in beats):raise ValueError('infeasible total duration')
    states={0:(F(0),())}
    for (_,lo,hi),target in zip(beats,targets):
        nxt={}
        for used,(cost,path) in states.items():
            for duration in range(lo,hi+1):
                amount=used+duration
                if amount<=total:
                    candidate=(cost+(duration-target)**2,path+(duration,))
                    if amount not in nxt or candidate<nxt[amount]:nxt[amount]=candidate
        states=nxt
    cost,path=states[total]
    return {'durations':list(path),'schedule':[(row[0],x) for row,x in zip(beats,path)],
            'certificate':{'total':sum(path),'objective':cost,'bounds_satisfied':True,'optimal':True}}
