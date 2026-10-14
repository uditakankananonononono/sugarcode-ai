"""Biological Computing - Living systems as computers.

PARTIAL: deterministic synchronous Boolean gene-regulatory circuit model, not
living cells, biological substrate computation or an experimentally validated
synthetic circuit. No host context, kinetic/noise or wet-lab design.
"""
SCOPE='synchronous Boolean gene circuit and cycle detection; no living substrate'


def run_circuit(initial,rules,steps=100):
    """Run exact Boolean state transition; detect first repeated full state.

    initial exactdict1..16 ASCII alnum/underscore genes -> built-in int0/1.
    rules list/tuple rows(gene,operation,inputlabels), mixed row container types
    accepted, exactly one per gene. Operations COPY,NOT (one input),AND,OR,XOR
    (1..16 inputs). Exactstr labels1..24, inputs known and unique. All updates
    simultaneous, label-sorted rows avoid mixed-container comparison. steps
    built-in int0..10000. Returns states up to first repeat or budget, attractor
    period/start if observed. No extrapolation beyond this deterministic model.
    """
    def label(x):
        if type(x) is not str or not 1<=len(x)<=24 or not x.isascii() or not all(c.isalnum() or c=='_' for c in x):
            raise ValueError('exact ASCII alphanumeric/underscore label length1..24 required')
    if type(initial) is not dict or not 1<=len(initial)<=16:
        raise ValueError('initial must be exactdict1..16 genes')
    for key,value in initial.items():
        label(key)
        if type(value) is not int or value not in (0,1):raise ValueError('gene values must be built-in int0/1')
    if type(steps) is not int or not 0<=steps<=10000:
        raise ValueError('steps must be built-in int0..10000')
    if type(rules) not in (list,tuple) or len(rules)!=len(initial):
        raise ValueError('exactly one rule per gene required')
    parsed={}
    for row in rules:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('rule must be list/tuple triple')
        gene,operation,inputs=row;label(gene)
        if gene not in initial or gene in parsed:raise ValueError('rule genes must be known and unique')
        if type(operation) is not str or operation not in ('COPY','NOT','AND','OR','XOR'):
            raise ValueError('operation must be exactstr COPY/NOT/AND/OR/XOR')
        if type(inputs) not in (list,tuple) or not 1<=len(inputs)<=16:
            raise ValueError('rule inputs must contain1..16 known unique genes')
        for key in inputs:label(key)
        if any(key not in initial for key in inputs) or len(set(inputs))!=len(inputs):
            raise ValueError('rule inputs must contain1..16 known unique genes')
        if operation in ('COPY','NOT') and len(inputs)!=1:
            raise ValueError('COPY/NOT require exactly one input')
        parsed[gene]=(operation,tuple(inputs))
    names=tuple(sorted(initial));state=tuple(initial[name] for name in names);states=[state];seen={state:0}
    for step in range(1,steps+1):
        old=dict(zip(names,state));values=[]
        for gene in names:
            operation,inputs=parsed[gene];bits=[old[key] for key in inputs]
            if operation=='COPY':value=bits[0]
            elif operation=='NOT':value=1-bits[0]
            elif operation=='AND':value=int(all(bits))
            elif operation=='OR':value=int(any(bits))
            else:value=sum(bits)%2
            values.append(value)
        state=tuple(values);states.append(state)
        if state in seen:
            return {'genes':names,'states':tuple(states),'cycle_start':seen[state],
                    'period':step-seen[state],'scope':SCOPE}
        seen[state]=step
    return {'genes':names,'states':tuple(states),'cycle_start':None,'period':None,'scope':SCOPE}
