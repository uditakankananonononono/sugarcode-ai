"""Row533 Data Lineage: supplied transform input-output provenance propagation.

Each dataset has supplied direct input indices. Compute ultimate source sets
and downstream impact sets; full DAG cycles refused. Caps32datasets/32inputs.
NOT_CLAIMED: real data flow observed, column lineage, external system access,
provenance authenticity, automatic discovery or live tracking.
"""


def lineage_sources(inputs):
    if type(inputs) not in (list,tuple):raise TypeError('inputs must be a list or tuple')
    n=len(inputs)
    if not 1<=n<=32:raise ValueError('dataset count must be between 1 and 32')
    if any(type(row) not in (list,tuple) or len(row)>32 for row in inputs):raise ValueError('datasets must contain at most 32 input indices')
    for i,row in enumerate(inputs):
        if any(type(j) is not int or not 0<=j<n or j==i for j in row):raise ValueError('inputs must contain nonbool valid nonself indices')
        if len(set(row))!=len(row):raise ValueError('input indices must be unique')
    sources={};ancestors={};pending=set(range(n))
    while pending:
        ready=[i for i in sorted(pending) if all(j in sources for j in inputs[i])]
        if not ready:raise ValueError('lineage graph must be acyclic')
        i=ready[0]
        sources[i]=set().union(*(sources[j] for j in inputs[i])) if inputs[i] else {i}
        ancestors[i]=set(inputs[i]).union(*(ancestors[j] for j in inputs[i]));pending.remove(i)
    return {'ultimate_sources':[sorted(sources[i]) for i in range(n)],
            'downstream_impact':[[j for j in range(n) if i in ancestors[j]] for i in range(n)],'lineage_validated':False}
