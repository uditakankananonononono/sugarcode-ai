"""Row 289 Interaction Design: exact finite interaction flow planning.

Finds a minimum-effort user interaction sequence through supplied states and
labeled transitions. Returns reachable-state and unreachable-goal diagnostics.
Ties preserve supplied transition order. Nonnegative effort permits exact
Dijkstra search with bounded state and transition counts.
NOT_CLAIMED: engagement or delight validation, visual UI, psychological
prediction, invented transitions, or autonomous user interaction.
"""
from fractions import Fraction


def _label(v):
    if type(v) is not str:raise TypeError('labels must be strings')
    if not 1<=len(v)<=80:raise ValueError('label length must be between 1 and 80')
    if not v.strip():raise ValueError('labels must not be blank')
    return v


def _effort(v):
    if type(v) not in (int,Fraction):raise TypeError('effort must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('effort must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('effort must fit 32 bits')
    if v<0:raise ValueError('effort must be nonnegative')
    return Fraction(v)


def plan_interaction(states,transitions,start,goal):
    if type(states) not in (list,tuple) or type(transitions) not in (list,tuple):
        raise TypeError('states and transitions must be lists or tuples')
    if not 1<=len(states)<=32:raise ValueError('state count must be between 1 and 32')
    if len(transitions)>128:raise ValueError('transition count must not exceed 128')
    if any(type(t) not in (list,tuple) or len(t)!=4 for t in transitions):
        raise ValueError('transitions must have source action destination effort')
    names=[_label(v) for v in states];s=_label(start);g=_label(goal)
    if len(set(names))!=len(names):raise ValueError('states must be unique')
    if s not in names or g not in names:raise ValueError('start and goal must be known states')
    edges=[(_label(a),_label(b),_label(c),_effort(d)) for a,b,c,d in transitions]
    if any(a not in names or c not in names for a,b,c,d in edges):
        raise ValueError('transition endpoints must be known states')
    dist={s:Fraction(0)};paths={s:[]};settled=set()
    while len(settled)<len(dist):
        node=min((v for v in dist if v not in settled),key=dist.__getitem__)
        settled.add(node)
        for index,(a,action,b,cost) in enumerate(edges):
            if a!=node or b in settled:continue
            value=dist[node]+cost
            if b not in dist or value<dist[b]:
                dist[b]=value;paths[b]=paths[node]+[index]
    if g not in dist:raise ValueError('goal is unreachable')
    ids=paths[g]
    return {'transition_indices':ids,'actions':[edges[i][1] for i in ids],
            'state_path':[s]+[edges[i][2] for i in ids],'total_effort':dist[g],
            'reachable_states':sorted(dist),'engagement_validated':False}
