"""Quantum Networking - Entanglement distribution.

PARTIAL: exact finite-size routing over independent Werner-state elementary
links with probabilistic Bell swaps. No network hardware or actual entanglement
distribution. Static route optimization only; no repeat-until-success scheduling.
"""
from math import isfinite


def best_entanglement_route(edges, source, target, swap_success=1.0):
    """Choose simple route maximizing per-attempt singlet-fraction yield.

    Undirected edge tuples (u,v,success,fidelity), 1..20 edges, <=10 nodes, no
    parallel/self edges. Fidelity in [0.25,1] parameterizes a Werner state.
    Swapping multiplies visibilities (4F-1)/3; each internal swap contributes
    swap_success. Objective success*(final_fidelity), not distillable key rate.
    Ties choose lexicographic path. Return None if disconnected. No zero-hop route.
    """
    def label(x):
        if type(x) is not str or not x or len(x)>24 or not x.isascii() or not x.isalnum():
            raise ValueError('node labels must be 1..24 ASCII alphanumeric strings')
    label(source);label(target)
    if source==target:
        raise ValueError('source and target must differ')
    if type(swap_success) not in (int,float) or not isfinite(swap_success) or not 0<=swap_success<=1:
        raise ValueError('swap_success must be finite built-in real in [0,1]')
    if type(edges) not in (list,tuple) or not 1<=len(edges)<=20:
        raise ValueError('edges must contain 1..20 edge tuples')
    adjacency={};seen=set()
    for edge in edges:
        if type(edge) is not tuple or len(edge)!=4:
            raise ValueError('each edge must be an exact four-item tuple')
        u,v,p,f=edge;label(u);label(v)
        if u==v or tuple(sorted((u,v))) in seen:
            raise ValueError('self or parallel edges refused')
        seen.add(tuple(sorted((u,v))))
        for value in (p,f):
            if type(value) not in (int,float) or not isfinite(value):
                raise ValueError('edge probabilities must be finite built-in reals')
        if not 0<=p<=1 or not .25<=f<=1:
            raise ValueError('success/fidelity outside [0,1]/[0.25,1]')
        adjacency.setdefault(u,[]).append((v,p,f));adjacency.setdefault(v,[]).append((u,p,f))
    if len(adjacency)>10:
        raise ValueError('at most 10 nodes supported')
    if source not in adjacency or target not in adjacency:
        raise ValueError('source and target must occur in edges')
    best=None
    def visit(path,success,visibility):
        nonlocal best
        u=path[-1]
        if u==target:
            fidelity=(1+3*visibility)/4
            result={'path':tuple(path),'success_probability':success,'fidelity':fidelity,
                    'yield':success*fidelity,'swaps':len(path)-2,
                    'scope':'independent Werner links; one attempt; no physical distribution'}
            if best is None or result['yield']>best['yield'] or (result['yield']==best['yield'] and result['path']<best['path']):
                best=result
            return
        for v,p,f in adjacency[u]:
            if v not in path:
                visit(path+[v],success*p*(swap_success if len(path)>1 else 1),visibility*(4*f-1)/3)
    visit([source],1.0,1.0)
    return best
