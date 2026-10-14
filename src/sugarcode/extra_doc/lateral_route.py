"""Row 865, Lateral Thinking - Approaches indirectly: the way around a direct link.

lateral_route takes edges, a list or tuple of 1 to 10 (a, b) tuples naming
two ends of an undirected link, start and goal. Every end, start and goal is a
printable ASCII string of 1 to 12 characters (control characters are refused).
The two ends of an edge differ, no pair repeats in either order, and the edges
name at most 8 different nodes. start and goal differ and both are named in
edges.
The direct link between start and goal, when there is one, is set aside, and
the shortest way around it is found over the other links. Among shortest ways,
the one whose node list is smallest in text order is returned.
Returns direct (True when edges contain the link between start and goal), path
(the node list from start to goal over the other links, None when there is
none), hops (the number of links on path, None without a path) and detour
(hops minus 1, the extra links compared with the direct one, None without a
path).
Checks, in this order: edges type, edges size, each edge (shape, first end,
second end, ends differ), distinct edges, node count, start, goal, start and
goal differ, start and goal named.
NOT_CLAIMED: real lateral thinking, creativity of the detour, weighted or
directed routes, learner insight, production readiness.
"""

SCOPE = 'PARTIAL: shortest way around a direct link in a supplied small graph, no thinking is assessed'
NOT_CLAIMED = ('real lateral thinking', 'creativity of the detour', 'weighted or directed routes',
               'learner insight', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def lateral_route(edges, start, goal):
    if type(edges) not in (list, tuple):
        raise TypeError('edges must be a list or tuple')
    if not 1 <= len(edges) <= 10:
        raise ValueError('edges must contain 1 to 10 entries')
    links = []
    for e in edges:
        if type(e) not in (list, tuple) or len(e) != 2:
            raise ValueError('each edge must be an (a, b) tuple')
        a, b = e
        if not _label(a):
            raise ValueError('each first end must be a printable ASCII string of 1 to 12 characters')
        if not _label(b):
            raise ValueError('each second end must be a printable ASCII string of 1 to 12 characters')
        if a == b:
            raise ValueError('the ends of an edge must differ')
        links.append(frozenset((a, b)))
    if len(set(links)) != len(links):
        raise ValueError('edges must be distinct')
    nodes = set().union(*links)
    if len(nodes) > 8:
        raise ValueError('edges must name at most 8 nodes')
    if not _label(start):
        raise ValueError('start must be a printable ASCII string of 1 to 12 characters')
    if not _label(goal):
        raise ValueError('goal must be a printable ASCII string of 1 to 12 characters')
    if start == goal:
        raise ValueError('start and goal must differ')
    if start not in nodes or goal not in nodes:
        raise ValueError('start and goal must be named in edges')
    direct = frozenset((start, goal)) in links
    near = {n: set() for n in nodes}
    for link in links:
        if link == frozenset((start, goal)):
            continue
        a, b = link
        near[a].add(b)
        near[b].add(a)
    dist = {goal: 0}
    frontier = [goal]
    while frontier:
        nxt = []
        for n in frontier:
            for m in near[n]:
                if m not in dist:
                    dist[m] = dist[n] + 1
                    nxt.append(m)
        frontier = nxt
    if start not in dist:
        return {'direct': direct, 'path': None, 'hops': None, 'detour': None}
    path = [start]
    while path[-1] != goal:
        path.append(min(m for m in near[path[-1]] if dist.get(m) == dist[path[-1]] - 1))
    return {'direct': direct, 'path': path, 'hops': dist[start], 'detour': dist[start] - 1}
