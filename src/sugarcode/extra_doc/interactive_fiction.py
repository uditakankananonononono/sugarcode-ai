"""Row 278, Interactive Fiction: exact analysis and generation of branching stories.

A story is a dict {node_id: [(choice_label, target_id), ...]} with a start node. A node
with no choices is an ending. analyse_story returns, exactly:
- unreachable: nodes not reachable from start (sorted);
- endings: reachable ending nodes (sorted); dead_end_free: every reachable node can
  reach some ending (no trap loop);
- has_cycle: some reachable node can return to itself;
- depth: for each reachable node, the fewest choices from the start (BFS);
- shortest_to_ending: fewest choices to any ending (None when no ending is reachable);
- simple_paths: number of start-to-ending paths that never revisit a node (counted by
  depth first search; the search is bounded by the node cap).
branching_skeleton(depth, branching) builds the complete tree: node 'n0' at the root,
nodes numbered breadth first, every non-leaf node has `branching` labelled choices
("choice 1" ... "choice b"), the leaves are the endings. It returns the story and the
analysis of it, so the counts are certified by analyse_story.
Caps: 1 to 30 nodes; the path search stops with an error after 100000 steps; ids 1 to 20 printable ASCII characters; 0 to 6 choices per node;
labels 1 to 60 printable ASCII characters; skeleton depth 0 to 4, branching 1 to 3 with
at most 30 nodes. Order of checks: nodes in dict order (id, then that node's choices), then start,
then every choice target, and only then any search.

NOT_CLAIMED: graph structure only. No story text is written or judged, nothing says the
branches are meaningful, balanced or fun, and no game engine, save system or UI is
involved. No clinical or wet-lab claim.
"""
from collections import deque

MAX_NODES, MAX_CHOICES, MAX_ID, MAX_LABEL, MAX_WALK = 30, 6, 20, 60, 100000


def _text(v, cap, what):
    if type(v) is not str:
        raise TypeError(what + ' must be str')
    if not 1 <= len(v) <= cap or any(not 32 <= ord(c) <= 126 for c in v):
        raise ValueError('%s must be 1 to %d printable ASCII characters' % (what, cap))


def analyse_story(story, start):
    if type(story) is not dict:
        raise TypeError('story must be a dict')
    if not 1 <= len(story) <= MAX_NODES:
        raise ValueError('node count must be between 1 and 30')
    for k, ch in story.items():
        _text(k, MAX_ID, 'node id')
        if type(ch) not in (list, tuple):
            raise TypeError('choices must be a list or tuple of (label, target) pairs')
        if len(ch) > MAX_CHOICES:
            raise ValueError('at most 6 choices per node')
        for c in ch:
            if type(c) not in (list, tuple) or len(c) != 2:
                raise TypeError('choices must be a list or tuple of (label, target) pairs')
            _text(c[0], MAX_LABEL, 'choice label')
            if type(c[1]) is not str:
                raise TypeError('choice target must be str')
    if type(start) is not str:
        raise TypeError('start must be str')
    if start not in story:
        raise ValueError('start is not a node')
    for k, ch in story.items():
        for c in ch:
            if c[1] not in story:
                raise ValueError('choice target is not a node')
    depth = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        for _, v in story[u]:
            if v not in depth:
                depth[v] = depth[u] + 1
                q.append(v)
    reach = sorted(depth)
    endings = sorted(u for u in reach if not story[u])
    unreachable = sorted(set(story) - set(depth))
    # nodes that can reach an ending: backwards closure
    good = set(endings)
    changed = True
    while changed:
        changed = False
        for u in reach:
            if u not in good and any(v in good for _, v in story[u]):
                good.add(u)
                changed = True
    # cycle: a reachable node that can reach itself in at least one step
    def reaches_self(s):
        seen, stack = set(), [v for _, v in story[s]]
        while stack:
            x = stack.pop()
            if x == s:
                return True
            if x in seen:
                continue
            seen.add(x)
            stack.extend(v for _, v in story[x])
        return False
    has_cycle = any(reaches_self(u) for u in reach)
    paths = 0
    calls = 0

    def walk(u, on):
        nonlocal paths, calls
        calls += 1
        if calls > MAX_WALK:
            raise ValueError('path search too large')
        if not story[u]:
            paths += 1
            return
        for _, v in story[u]:
            if v not in on:
                walk(v, on | {v})

    walk(start, {start})
    shortest = min((depth[e] for e in endings), default=None)
    return {'reachable': reach, 'unreachable': unreachable, 'endings': endings,
            'dead_end_free': len(good) == len(reach), 'has_cycle': has_cycle,
            'depth': {u: depth[u] for u in reach}, 'shortest_to_ending': shortest,
            'simple_paths': paths}


def branching_skeleton(depth, branching):
    if type(depth) is not int or type(branching) is not int:
        raise TypeError('depth and branching must be nonbool ints')
    if not 0 <= depth <= 4:
        raise ValueError('depth must be between 0 and 4')
    if not 1 <= branching <= 3:
        raise ValueError('branching must be between 1 and 3')
    total = sum(branching ** d for d in range(depth + 1))
    if total > MAX_NODES:
        raise ValueError('skeleton would exceed 30 nodes')
    story = {}
    first_leaf = total - branching ** depth
    for i in range(total):
        if i < first_leaf:
            story['n%d' % i] = [('choice %d' % (j + 1), 'n%d' % (i * branching + 1 + j)) for j in range(branching)]
        else:
            story['n%d' % i] = []
    return {'story': story, 'start': 'n0', 'analysis': analyse_story(story, 'n0')}
