"""Exact finite-horizon deterministic Bellman planning on supplied transitions.
NOT_CLAIMED: authentic dynamics; arbitrary infinite horizon; execution of plans;
model completeness; runtime integration.
"""
from fractions import Fraction
import math


def plan(states,stages,initial,terminal_costs):
    def label(v):
        if type(v) is not str or not 1<=len(v)<=80:raise ValueError('state/action label 1..80 chars')
        return v
    def number(v):
        if type(v) not in (int,float) or not -1000<=v<=1000 or not math.isfinite(v):raise ValueError('strict finite Bellman cost within -1000..1000')
        return Fraction(str(v))
    if type(states) is not list or not 1<=len(states)<=20:raise ValueError('1..20 states before scan')
    names=[label(v) for v in states]
    if len(set(names))!=len(names):raise ValueError('unique Bellman states')
    if type(initial) is not str or initial not in names:raise ValueError('initial state in supplied menu')
    if type(stages) is not list or not 1<=len(stages)<=20:raise ValueError('1..20 stages before scan')
    if type(terminal_costs) is not dict or set(terminal_costs)!=set(names):raise ValueError('terminal cost for every supplied state')
    terminal={k:number(v) for k,v in terminal_costs.items()};parsed=[]
    for stage in stages:
        if type(stage) is not list or len(stage)>100:raise ValueError('0..100 transitions per stage before scan')
        edges=[];seen=set()
        for row in stage:
            if type(row) is not dict or set(row)!={'state','action','next','cost'}:raise ValueError('exact state/action/next/cost fields')
            state=label(row['state']);action=label(row['action']);nxt=label(row['next'])
            if state not in names or nxt not in names:raise ValueError('transition states in menu')
            if (state,action) in seen:raise ValueError('unique state/action per stage')
            seen.add((state,action));edges.append((state,action,nxt,number(row['cost'])))
        parsed.append(edges)
    value=terminal;tables=[None]*(len(stages)+1);tables[-1]=terminal;policies=[None]*len(stages)
    for t in range(len(stages)-1,-1,-1):
        current={};policy={}
        for state in names:
            choices=[(cost+value[nxt],action,nxt) for origin,action,nxt,cost in parsed[t] if origin==state and nxt in value]
            if choices:
                total,action,nxt=min(choices);current[state]=total;policy[state]=(action,nxt)
        value=current;tables[t]=current;policies[t]=policy
    route=[];state=initial
    if state in value:
        for t,policy in enumerate(policies):
            action,nxt=policy[state];route.append({'stage':t,'state':state,'action':action,'next':nxt});state=nxt
    return {'status':'optimal_in_supplied_finite_model' if initial in value else 'no_terminal_reaching_plan',
            'initial_cost_fraction':str(value[initial]) if initial in value else None,'plan':route,
            'value_tables_fraction':[{k:str(v) for k,v in sorted(table.items())} for table in tables],
            'terminal_state':state if route else None,'tie_break':'lowest action label then next-state label',
            'recurrence':'V_t(s)=min_a(cost_t(s,a)+V_(t+1)(next)); dead states omitted','external_effects':[]}
