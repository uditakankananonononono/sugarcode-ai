"""Row538 Data Mesh Design: supplied product-owner dependency contracts.
For each consumer->provider product dependency, identify cross-domain boundary
contract pairs and aggregate the product-edge counts by ordered domain pair.
Caps32products/128edges/16domains. NOT_CLAIMED: decentralized infrastructure,
actual ownership, access permission, API contracts or live system changes.
"""


def mesh_contracts(owners,dependencies):
    if type(owners) not in (list,tuple) or type(dependencies) not in (list,tuple):raise TypeError('inputs must be lists or tuples')
    n=len(owners)
    if not 1<=n<=32 or len(dependencies)>128:raise ValueError('product cap is 32 and dependency cap is 128')
    if any(type(o) is not int or not 0<=o<16 for o in owners):raise ValueError('owners must be nonbool domain indices 0 through 15')
    if any(type(e) not in (list,tuple) or len(e)!=2 for e in dependencies):raise ValueError('dependencies must contain consumer and provider')
    if any(type(i) is not int or not 0<=i<n for e in dependencies for i in e):raise ValueError('products must be nonbool valid indices')
    edges=[tuple(e) for e in dependencies]
    if any(a==b for a,b in edges) or len(set(edges))!=len(edges):raise ValueError('dependencies must be distinct and nonself')
    contracts=[];counts={}
    for a,b in sorted(edges):
        if owners[a]!=owners[b]:
            contracts.append([a,b]);pair=(owners[a],owners[b]);counts[pair]=counts.get(pair,0)+1
    return {'cross_domain_products':contracts,'domain_contract_counts':[[a,b,v] for (a,b),v in sorted(counts.items())],'mesh_deployed':False}
