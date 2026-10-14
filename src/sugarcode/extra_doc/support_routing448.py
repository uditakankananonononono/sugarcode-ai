"""Row 448 Support System Design - Creates help infrastructure.
Choose deterministic shortest escalation routes through supplied support queues.
Each queue is (resolution cost, outgoing queue indices); resolution cost None
means no terminal resolution. Each hop costs one, followed by terminal cost.
Ties choose lexicographically smallest simple queue-index path. Cycles allowed.
1..8 queues, costs 0..10**6, 0..64 supplied starting queues. Exact integer costs.
NOT_CLAIMED: actual infrastructure, response time, resolved tickets, suitability,
service availability, integrations, deployment, external communication.
"""

def route(queues, starts):
    if type(queues) is not list or not 1<=len(queues)<=8:
        raise ValueError('1..8 queues before scan')
    if type(starts) is not list or len(starts)>64:
        raise ValueError('0..64 starts before scan')
    n=len(queues)
    for q in queues:
        if type(q) is not tuple or len(q)!=2:raise ValueError('queue pair cost outgoing')
        if type(q[1]) is not list or len(q[1])>8:raise ValueError('0..8 outgoing before scan')
    for cost,edges in queues:
        if cost is not None and (type(cost) is not int or not 0<=cost<=10**6):
            raise ValueError('terminal cost None or bounded integer')
        if any(type(j) is not int or not 0<=j<n for j in edges):
            raise ValueError('valid integer outgoing indices')
        if len(set(edges))!=len(edges):raise ValueError('unique outgoing indices')
    if any(type(j) is not int or not 0<=j<n for j in starts):
        raise ValueError('valid integer starting indices')
    routes=[]
    for start in starts:
        stack=[(start,)];options=[]
        while stack:
            path=stack.pop();cost,edges=queues[path[-1]]
            if cost is not None:options.append((len(path)-1+cost,path))
            for j in edges:
                if j not in path:stack.append(path+(j,))
        if options:
            cost,path=min(options);routes.append({'path':path,'cost':cost,'terminal':path[-1]})
        else:routes.append(None)
    return {'routes':routes,'infrastructure_created':False}
