"""Doc row1738 Longitudinal Research: PARTIAL supplied repeated-score change.

Rows exact list1..100 tuples(id,time,score); nonblank exact str<=80 IDs, time
exact int0..100, score exact int0..1000. Repeated IDs allowed, id-time pair unique.
Group IDs sorted, observations sorted time. Return first/last, signed change,
exact per-time slope (None for single observation). No causal/trajectory validity.
"""
from fractions import Fraction


def summarize(rows):
    if type(rows) is not list or not 1<=len(rows)<=100:
        raise ValueError('rows must be an exact list with 1..100 entries')
    seen=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('row must be an id time score tuple')
        name,time,score=row
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip():
            raise ValueError('IDs must be nonblank exact strings of 1..80 characters')
        if type(time) is not int or not 0<=time<=100:raise ValueError('time must be an integer in 0..100')
        if type(score) is not int or not 0<=score<=1000:raise ValueError('score must be an integer in 0..1000')
        if (name,time) in seen:raise ValueError('ID time pairs must be unique')
        seen.add((name,time))
    groups={}
    for n,t,s in rows:groups.setdefault(n,[]).append((t,s))
    result=[]
    for n,points in sorted(groups.items()):
        ordered=sorted(points);first,last=ordered[0],ordered[-1];delta=last[1]-first[1]
        slope=Fraction(delta,last[0]-first[0]) if len(points)>1 else None
        result.append((n,first,last,delta,None if slope is None else (slope.numerator,slope.denominator)))
    return {'changes':result,'claim':'PARTIAL','trajectory_validated':False}
