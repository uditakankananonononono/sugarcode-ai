"""Row 262 Character Development: finite compatible persona and belief arc.

Creates a multidimensional fictional person by selecting one supplied value
for each dimension, excluding forbidden pairs, then applying supplied events
that revise one belief. Deterministic first feasible persona, with explicit
before/after motivation and contradiction records.
NOT_CLAIMED: open-ended literary invention, originality, psychological realism,
quality validation, natural prose generation, or autonomous publication.
"""
from itertools import product


def _text(value):
    if type(value) is not str:raise TypeError('labels must be strings')
    if not 1 <= len(value) <= 80:raise ValueError('label length must be between 1 and 80')
    if not value.strip():raise ValueError('labels must not be blank')
    return value


def develop_character(dimensions, forbidden_pairs, events):
    if type(dimensions) is not dict:raise TypeError('dimensions must be a dict')
    if not 2 <= len(dimensions) <= 6:raise ValueError('dimension count must be between 2 and 6')
    if type(forbidden_pairs) not in (list,tuple) or type(events) not in (list,tuple):
        raise TypeError('rules and events must be lists or tuples')
    if len(forbidden_pairs)>64 or len(events)>32:raise ValueError('rule count must not exceed 64 and event count 32')
    # Shape and work caps precede label scanning and Cartesian enumeration.
    count=1
    for options in dimensions.values():
        if type(options) not in (list,tuple) or not 1<=len(options)<=4:
            raise ValueError('each dimension must have between 1 and 4 options')
        count*=len(options)
    if count>4096:raise ValueError('persona search must not exceed 4096 candidates')
    for rule in forbidden_pairs:
        if type(rule) not in (list,tuple) or len(rule)!=4:raise ValueError('forbidden pairs must have four fields')
    for event in events:
        if type(event) not in (list,tuple) or len(event)!=5:raise ValueError('events must have five fields')
    keys=[_text(k) for k in dimensions]
    opts=[[_text(v) for v in dimensions[k]] for k in keys]
    if any(len(set(values))!=len(values) for values in opts):raise ValueError('dimension options must be unique')
    rules=[tuple(_text(v) for v in rule) for rule in forbidden_pairs]
    for a,x,b,y in rules:
        if a not in dimensions or b not in dimensions or a==b or x not in dimensions[a] or y not in dimensions[b]:
            raise ValueError('forbidden pair must reference distinct known dimensions and options')
    evs=[tuple(_text(v) for v in event) for event in events]
    for name,key,expected,revised,motive in evs:
        if key not in dimensions:raise ValueError('event must reference a known dimension')
    persona=None
    for values in product(*opts):
        candidate=dict(zip(keys,values))
        if not any(candidate[a]==x and candidate[b]==y for a,x,b,y in rules):
            persona=candidate;break
    if persona is None:raise ValueError('no compatible persona exists')
    state=persona.copy();arc=[]
    for name,key,expected,revised,motive in evs:
        before=state[key];applied=before==expected
        if applied:state[key]=revised
        contradictions=[rule for rule in rules if state[rule[0]]==rule[1] and state[rule[2]]==rule[3]]
        arc.append({'event':name,'dimension':key,'before':before,'after':state[key],
                    'applied':applied,'motivation':motive,'contradictions':contradictions})
    return {'persona':persona,'final_persona':state,'arc':arc,'creative_quality_claimed':False}
