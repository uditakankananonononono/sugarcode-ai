"""Row1974 Graph-of-Thought: exact bounded directed state-path search.
Nodes exact list1..8 unique nonblank exact str1..80. Edges exact list0..56
(source,target,cost) tuples,known distinct exact labels,unique ordered pair,
cost exact int0..1000. Start/goal known exact labels. Enumerate simple paths;
choose min total cost,then fewer edges,then node input-index tuple. Return path,
cost or None if unreachable. No generated reasoning/correctness claim.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def best_path(nodes,edges,start,goal):
    if type(nodes) is not list or not 1<=len(nodes)<=8 or any(not _label(x) for x in nodes) or len(set(nodes))!=len(nodes):raise ValueError('nodes must be exact list1..8 unique valid labels')
    if not _label(start) or start not in nodes:raise ValueError('start must be known valid label')
    if not _label(goal) or goal not in nodes:raise ValueError('goal must be known valid label')
    if type(edges) is not list or len(edges)>56:raise ValueError('edges must be exact list0..56')
    seen=set()
    for row in edges:
        if type(row) is not tuple or len(row)!=3:raise ValueError('edge must be exact source target cost tuple')
        a,b,c=row
        if not _label(a) or not _label(b) or a not in nodes or b not in nodes or a==b:raise ValueError('endpoints must be distinct known valid labels')
        if (a,b) in seen:raise ValueError('ordered pairs must be unique')
        seen.add((a,b))
        if type(c) is not int or not 0<=c<=1000:raise ValueError('cost must be exact int0..1000')
    rank={n:i for i,n in enumerate(nodes)};best=None;chosen=None;stack=[([start],0)]
    while stack:
        path,cost=stack.pop();current=path[-1]
        if current==goal:
            key=(cost,len(path)-1,tuple(rank[n] for n in path))
            if best is None or key<best:best=key;chosen=path
            continue
        for a,b,c in edges:
            if a==current and b not in path:stack.append((path+[b],cost+c))
    return {'path':chosen,'cost':None if best is None else best[0],'reasoning_validated':False}
