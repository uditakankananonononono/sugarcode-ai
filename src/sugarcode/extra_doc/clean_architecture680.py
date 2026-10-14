"""Doc row680 Clean Architecture: PARTIAL supplied dependency layer audit.

layers exact dict1..100 labels to exact nonbool integer0..10 (0 is inner).
Edges exact list0..500 tuples(source,target), known exact str IDs. Repeats allowed.
A dependency is outward iff target layer exceeds source layer. Report input
indexes of outward/same/inward edges, preserving duplicates. No code parsing,
architectural completeness or actual software correctness claim.
"""


def audit(layers,edges):
    if type(layers) is not dict or not 1<=len(layers)<=100:
        raise ValueError('layers must be an exact dict with 1..100 entries')
    for name,layer in layers.items():
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip():
            raise ValueError('IDs must be nonblank exact strings of 1..80 characters')
        if type(layer) is not int or not 0<=layer<=10:
            raise ValueError('layers must be integers in 0..10')
    if type(edges) is not list or len(edges)>500:
        raise ValueError('edges must be an exact list with 0..500 entries')
    for row in edges:
        if type(row) is not tuple or len(row)!=2 or any(type(x) is not str or x not in layers for x in row):
            raise ValueError('edges must be exact known ID pair tuples')
    return {'outward':[i for i,(a,b) in enumerate(edges) if layers[b]>layers[a]],
            'same':[i for i,(a,b) in enumerate(edges) if layers[b]==layers[a]],
            'inward':[i for i,(a,b) in enumerate(edges) if layers[b]<layers[a]],
            'claim':'PARTIAL','code_validated':False}
