"""Row 1044 Graphical Models - Represent dependencies.

Delete conditioned nodes from a finite undirected simple graph, return its
connected components and whether two remaining nodes are separated. If not,
return the lexicographically smallest shortest witness path. Nodes are ASCII
lowercase identifiers (1..8 letters). Exact containers only; 2..12 unique
nodes, 0..30 unique undirected edges, 0..12 unique conditioned nodes. Input
caps precede scans. Separation is a graph property, not a causal conclusion.
NOT_CLAIMED: directed causal inference, probability estimation, graph learning,
production readiness. No fitted graphical model is claimed.
"""
ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
SCOPE = 'PARTIAL: undirected graph separation only'
NOT_CLAIMED = ('directed causal inference', 'probability estimation', 'graph learning', 'production readiness')


def _label(value):
    if type(value) is not str or not 1 <= len(value) <= 8:
        raise ValueError('label must be an exact string of 1..8 lowercase ASCII letters')
    if any(ch not in ALPHABET for ch in value):
        raise ValueError('label must be an exact string of 1..8 lowercase ASCII letters')


def separate(data):
    if type(data) is not dict or set(data) != {'nodes', 'edges', 'given', 'source', 'target'}:
        raise ValueError('exact dict with nodes, edges, given, source, target required')
    nodes, edges, given = data['nodes'], data['edges'], data['given']
    if type(nodes) is not list or not 2 <= len(nodes) <= 12:
        raise ValueError('nodes must be a list of 2..12 identifiers')
    if type(edges) is not list or len(edges) > 30:
        raise ValueError('edges must be a list of 0..30 pairs')
    if type(given) is not list or len(given) > 12:
        raise ValueError('given must be a list of 0..12 identifiers')
    for node in nodes:
        _label(node)
    if len(set(nodes)) != len(nodes):
        raise ValueError('nodes must be unique')
    for node in given:
        _label(node)
        if node not in nodes:
            raise ValueError('conditioned node is undeclared')
    if len(set(given)) != len(given):
        raise ValueError('conditioned nodes must be unique')
    source, target = data['source'], data['target']
    _label(source)
    _label(target)
    if source not in nodes or target not in nodes or source == target:
        raise ValueError('distinct declared endpoints required')
    if source in given or target in given:
        raise ValueError('endpoints must not be conditioned')
    adjacency = {node: set() for node in nodes if node not in given}
    seen_edges = set()
    for edge in edges:
        if type(edge) is not list or len(edge) != 2:
            raise ValueError('edge must be an exact list pair')
        a, b = edge
        _label(a)
        _label(b)
        if a not in nodes or b not in nodes or a == b:
            raise ValueError('edge must join distinct declared nodes')
        key = tuple(sorted((a, b)))
        if key in seen_edges:
            raise ValueError('duplicate undirected edge')
        seen_edges.add(key)
        if a in adjacency and b in adjacency:
            adjacency[a].add(b)
            adjacency[b].add(a)
    paths = {source: [source]}
    queue = [source]
    for node in queue:
        for neighbor in sorted(adjacency[node]):
            if neighbor not in paths:
                paths[neighbor] = paths[node] + [neighbor]
                queue.append(neighbor)
    components = []
    remaining = set(adjacency)
    while remaining:
        start = min(remaining)
        visited = {start}
        pending = [start]
        for node in pending:
            for neighbor in sorted(adjacency[node]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    pending.append(neighbor)
        components.append(sorted(visited))
        remaining.difference_update(visited)
    return {'separated': target not in paths, 'path': paths.get(target, []),
            'components': components, 'claims': [False, False, False, False]}
