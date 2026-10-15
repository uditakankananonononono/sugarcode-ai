"""Customer Journey Mapping (canonical367): PARTIAL empirical absorbing touchpoints.

states exact int1..3 transient touchpoint IDs0..states-1; IDstates=failure,
IDstates+1=success. journeys exact list1..6 exact tuple2..6 of exact IDs. Every
journey starts transient, only final ID may be absorbing and final must be
absorbing. Every transient state must occur before an endpoint. Count supplied
adjacent transitions, normalize outgoing frequencies, compute fundamental
matrix N=(I-Q)^-1, expected visits (including current state), expected steps to
absorption, success probabilities. Complete finite paths ensure absorption in
the empirical transition model; not evidence of real customer behavior.
Validation states, outer, each path shape/each scalar then transient-prefix and
absorbing-end requirement before next path; transient coverage last.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: exact empirical absorbing touchpoint journey frequencies visits and completion'
NOT_CLAIMED=('authentic customer behavior','Markov validity','causal influence','future conversion','business advice')


def map_journeys(states,journeys):
    if type(states) is not int or not 1<=states<=3:raise ValueError('states must be exact int1..3')
    if type(journeys) is not list or not 1<=len(journeys)<=6:raise ValueError('journeys must be exact list1..6')
    covered=set();counts=[[0]*(states+2) for _ in range(states)]
    for path in journeys:
        if type(path) is not tuple or not 2<=len(path)<=6:raise ValueError('journey must be exact tuple2..6')
        for value in path:
            if type(value) is not int or not 0<=value<=states+1:raise ValueError('journey IDs must be exact declared ints')
        if any(value>=states for value in path[:-1]):raise ValueError('journey prefix must be transient')
        if path[-1]<states:raise ValueError('journey must end absorbing')
        covered.update(path[:-1])
        for a,b in zip(path,path[1:]):counts[a][b]+=1
    if covered!=set(range(states)):raise ValueError('all transient states must appear')
    transition=[tuple(F(v,sum(row)) for v in row) for row in counts]
    a=[[F(int(i==j))-transition[i][j] for j in range(states)]+[F(int(i==j)) for j in range(states)] for i in range(states)]
    for k in range(states):
        pivot=next(i for i in range(k,states) if a[i][k]);a[k],a[pivot]=a[pivot],a[k]
        scale=a[k][k];a[k]=[v/scale for v in a[k]]
        for i in range(states):
            if i!=k:
                scale=a[i][k];a[i]=[x-scale*y for x,y in zip(a[i],a[k])]
    visits=[tuple(row[states:]) for row in a]
    success=[sum((visits[i][j]*transition[j][-1] for j in range(states)),F(0)) for i in range(states)]
    return {'transition':transition,'visits':visits,'expected_steps':[sum(row,F(0)) for row in visits],
            'success_probability':success,'journey_validated':False}
