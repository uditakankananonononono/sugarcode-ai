"""Row 1189, Contact Tracing: supplied graph reachability only.

PARTIAL: enumerate shortest hop distances in a caller-supplied undirected
contact graph. No inference about infection, exposure risk, or real people.

trace_contacts(contacts, seeds, max_hops=2) accepts exact list/tuple containers.
Contacts: 0..64 exact list/tuple pairs of distinct ASCII identifiers; duplicate
undirected edges are refused. Identifiers are exact strings of 1..24 ASCII
letters, digits or underscore (no leading-character restriction). Seeds:
1..16 unique identifiers; a seed need not occur in an edge. max_hops is an
exact built-in int in 0..16. At most 64 distinct identifiers across edges and
seeds. Validate contacts in order, then seeds, then max_hops, then node cap.

Return distances as label-sorted (label, shortest distance from any seed)
rows for nodes within the budget; unreached is every supplied node outside
that set. Seed distance is zero. The inputs are not changed.
"""
from collections import deque

SCOPE = 'PARTIAL: supplied undirected graph hops only; no exposure assessment'
NOT_CLAIMED = (
    'does not identify real contacts',
    'does not estimate infection or exposure risk',
    'does not recommend testing, treatment or quarantine',
    'does not contact people or update public-health records',
)


def _label(value):
    if type(value) is not str:
        raise TypeError('identifier must be an exact string')
    if not 1 <= len(value) <= 24 or not all(
        c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'
        for c in value
    ):
        raise ValueError('identifier must be 1..24 ASCII word characters')


def trace_contacts(contacts, seeds, max_hops=2):
    if type(contacts) not in (list, tuple):
        raise TypeError('contacts must be an exact list or tuple')
    if len(contacts) > 64:
        raise ValueError('at most 64 contacts required')
    graph = {}
    edges = set()
    for edge in contacts:
        if type(edge) not in (list, tuple):
            raise TypeError('contact must be an exact list or tuple')
        if len(edge) != 2:
            raise ValueError('contact must contain exactly two identifiers')
        a, b = edge
        _label(a)
        _label(b)
        if a == b:
            raise ValueError('self contact is not allowed')
        pair = tuple(sorted((a, b)))
        if pair in edges:
            raise ValueError('duplicate undirected contact')
        edges.add(pair)
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    if type(seeds) not in (list, tuple):
        raise TypeError('seeds must be an exact list or tuple')
    if not 1 <= len(seeds) <= 16:
        raise ValueError('seeds must contain 1..16 identifiers')
    seen = set()
    for seed in seeds:
        _label(seed)
        if seed in seen:
            raise ValueError('seeds must be unique')
        seen.add(seed)
        graph.setdefault(seed, set())
    if type(max_hops) is not int:
        raise TypeError('max_hops must be an exact int')
    if not 0 <= max_hops <= 16:
        raise ValueError('max_hops must be 0..16')
    if len(graph) > 64:
        raise ValueError('at most 64 distinct identifiers required')
    distance = {seed: 0 for seed in seeds}
    pending = deque(seeds)
    while pending:
        current = pending.popleft()
        if distance[current] == max_hops:
            continue
        for neighbor in sorted(graph[current]):
            if neighbor not in distance:
                distance[neighbor] = distance[current] + 1
                pending.append(neighbor)
    return {
        'distances': sorted(distance.items()),
        'unreached': sorted(set(graph) - set(distance)),
        'scope': SCOPE,
        'not_claimed': list(NOT_CLAIMED),
    }
