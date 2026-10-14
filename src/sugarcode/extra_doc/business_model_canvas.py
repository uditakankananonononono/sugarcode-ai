"""Row 364 Business Model Canvas: bounded nine-block business logic graph.

Each standard block holds supplied entries; directed links connect flattened
entry indices. Returns block membership, direct links, transitive reachability
and isolated entries for checking missing logic connections. Cycles allowed.
Caps nine blocks, eight entries/block, 64 chars/entry, 128 links before scans.
NOT_CLAIMED: graphical canvas rendering, viable business model, researched
facts, inferred causal relationships, profitability or business execution.
"""
BLOCKS=('partners','activities','resources','value_propositions','relationships',
        'channels','segments','costs','revenues')


def map_canvas(blocks,links):
    if type(blocks) not in (list,tuple) or type(links) not in (list,tuple):
        raise TypeError('inputs must be lists or tuples')
    if len(blocks)!=9:raise ValueError('exactly nine blocks required')
    if len(links)>128:raise ValueError('at most 128 links allowed')
    if any(type(row) not in (list,tuple) or len(row)>8 for row in blocks):
        raise ValueError('blocks must contain at most eight entries')
    if any(type(edge) not in (list,tuple) or len(edge)!=2 for edge in links):
        raise ValueError('links must be pairs')
    nodes=[]
    for name,row in zip(BLOCKS,blocks):
        for label in row:
            if type(label) is not str or not 1<=len(label)<=64:
                raise ValueError('entries must be strings of length 1 through 64')
            nodes.append({'block':name,'entry':label})
    n=len(nodes);edges=[]
    for a,b in links:
        if any(type(i) is not int or not 0<=i<n for i in (a,b)) or a==b:
            raise ValueError('links must contain nonbool valid distinct entry indices')
        edges.append((a,b))
    if len(set(edges))!=len(edges):raise ValueError('links must be unique')
    direct=[[] for _ in nodes];connected=set()
    for a,b in edges:
        direct[a].append(b);connected.update((a,b))
    reachable=[]
    for start in range(n):
        seen=set();pending=list(direct[start])
        while pending:
            i=pending.pop()
            if i in seen:continue
            seen.add(i);pending.extend(direct[i])
        seen.discard(start);reachable.append(sorted(seen))
    return {'nodes':nodes,'links':[list(edge) for edge in edges],
            'reachable':reachable,'isolated':[i for i in range(n) if i not in connected],
            'business_viability_validated':False}
