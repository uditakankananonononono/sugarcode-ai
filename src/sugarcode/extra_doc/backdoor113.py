"""Row 113 Confound Identification - Spots variables that could distort results.

PARTIAL: exact graphical backdoor adjustment sets in a supplied ordered DAG.
Input exact dict parents, treatment, outcome. Parents is an exact list of 2..6
exact lists, row i containing at most i distinct exact integer indices 0..i-1.
Treatment and outcome are distinct exact integer indices. Remove arrows leaving
treatment; enumerate subsets excluding treatment, outcome and all descendants
of treatment in the original graph. A subset qualifies when it d-separates the
treatment and outcome in the modified graph, using ancestral moralization.
Return every qualifying subset (not only minimal), ordered by size then index
lexicographic order, as integer lists in adjustment_sets; descendants sorted
integer list; claims three False booleans. Empty qualifying set is meaningful.
NOT_CLAIMED: graph truth, hidden-confounder detection, causal effect estimation.
"""
from itertools import combinations
SCOPE = 'PARTIAL: exact supplied ordered-DAG graphical backdoor sets only'
NOT_CLAIMED = ('graph truth', 'hidden-confounder detection', 'causal effect estimation')


def identify(data):
    if type(data) is not dict or set(data) != {'parents', 'treatment', 'outcome'}:
        raise ValueError('exact dict with parents, treatment, outcome required')
    parents = data['parents']
    if type(parents) is not list or not 2 <= len(parents) <= 6:
        raise ValueError('parents must be an exact list of 2..6 rows')
    n = len(parents)
    for i, row in enumerate(parents):
        if type(row) is not list or len(row) > i:
            raise ValueError('parent rows must be exact lists of at most their index entries')
        for v in row:
            if type(v) is not int or not 0 <= v < i:
                raise ValueError('parents must be exact nonnegative integers preceding child')
        if len(set(row)) != len(row):
            raise ValueError('parent indices must be unique')
    for name in ('treatment', 'outcome'):
        v = data[name]
        if type(v) is not int or not 0 <= v < n:
            raise ValueError(name + ' must be an exact declared node index')
    t, y = data['treatment'], data['outcome']
    if t == y:
        raise ValueError('treatment and outcome must differ')
    descendants = set()
    for i, row in enumerate(parents):
        if t in row or any(p in descendants for p in row):
            descendants.add(i)
    graph = [[p for p in row if p != t] for row in parents]
    allowed = [i for i in range(n) if i not in descendants and i not in (t, y)]
    results = []
    for size in range(len(allowed)+1):
        for subset in combinations(allowed, size):
            ancestors = {t, y, *subset}
            for i in reversed(range(n)):
                if i in ancestors:
                    ancestors.update(graph[i])
            neighbors = {i: set() for i in ancestors}
            for i in ancestors:
                for p in graph[i]:
                    neighbors[i].add(p)
                    neighbors[p].add(i)
                for a, b in combinations(graph[i], 2):
                    neighbors[a].add(b)
                    neighbors[b].add(a)
            visited = set(subset)
            pending = [t]
            while pending:
                current = pending.pop()
                if current not in visited:
                    visited.add(current)
                    pending.extend(neighbors[current] - visited)
            if y not in visited:
                results.append(list(subset))
    return {'adjustment_sets': results, 'descendants': sorted(descendants), 'claims': [False, False, False]}
