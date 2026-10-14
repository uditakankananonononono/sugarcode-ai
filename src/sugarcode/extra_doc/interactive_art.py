"""Row 314 Interactive Art: responsive finite-state installation simulation.

Executes supplied (state,event,next_state,output) rules against a bounded
input event stream. Unmatched events leave state unchanged and emit nothing;
matched events create explicit responsive installation output records.
NOT_CLAIMED: physical installation, sensor acquisition, artistic quality,
visual rendering, audience engagement or autonomous deployment.
"""


def _label(v):
    if type(v) is not str:raise TypeError('labels must be strings')
    if not 1<=len(v)<=80:raise ValueError('label length must be between 1 and 80')
    if not v.strip():raise ValueError('labels must not be blank')
    return v


def simulate_installation(states,rules,initial_state,events):
    if any(type(v) not in (list,tuple) for v in (states,rules,events)):
        raise TypeError('states rules and events must be lists or tuples')
    if not 1<=len(states)<=16:raise ValueError('state count must be between 1 and 16')
    if len(rules)>64:raise ValueError('rule count must not exceed 64')
    if len(events)>256:raise ValueError('event count must not exceed 256')
    if any(type(rule) not in (list,tuple) or len(rule)!=4 for rule in rules):
        raise ValueError('rules must contain state event next_state output')
    names=[_label(v) for v in states];initial=_label(initial_state)
    if len(set(names))!=len(names):raise ValueError('states must be unique')
    if initial not in names:raise ValueError('initial state must be known')
    rs=[tuple(_label(v) for v in rule) for rule in rules];es=[_label(v) for v in events]
    if any(a not in names or c not in names for a,b,c,d in rs):
        raise ValueError('rule states must be known')
    mapping={}
    for a,b,c,d in rs:
        if (a,b) in mapping:raise ValueError('state event pairs must be unique')
        mapping[(a,b)]=(c,d)
    state=initial;trace=[];outputs=[]
    for index,event in enumerate(es):
        before=state;rule=mapping.get((state,event));output=None
        if rule is not None:
            state,output=rule;outputs.append(output)
        trace.append({'event_index':index,'event':event,'before':before,'after':state,'output':output})
    return {'final_state':state,'trace':trace,'outputs':outputs,'physical_execution_performed':False}
