"""Row 324 Landscape Design: exact finite outdoor zone placement.

Assigns supplied zone codes to up to six cells, honoring per-zone minimum
counts and forbidden adjacent zone pairs. Minimizes supplied per-cell costs;
ties retain supplied product order. Returns a coherent zone configuration.
Self adjacency (i,i) with forbidden (z,z) blocks zone z at cell i.
NOT_CLAIMED: ecology, drainage, horticulture, aesthetic quality, physical site
survey, rendered landscape or autonomous deployment.
"""
from itertools import product


def zone_landscape(options,costs,minimum_counts,adjacency,forbidden_pairs):
    if any(type(v) not in (list,tuple) for v in (options,costs,minimum_counts,adjacency,forbidden_pairs)):
        raise TypeError('inputs must be lists or tuples')
    n=len(options);k=len(minimum_counts)
    if not 1<=n<=6:raise ValueError('cell count must be between 1 and 6')
    if not 1<=k<=4:raise ValueError('zone count must be between 1 and 4')
    if len(costs)!=n:raise ValueError('cost rows must match cells')
    if len(adjacency)>15 or len(forbidden_pairs)>16:raise ValueError('adjacency and forbidden caps are 15 and 16')
    for opts,row in zip(options,costs):
        if type(opts) not in (list,tuple) or not 1<=len(opts)<=4:raise ValueError('each cell must have between 1 and 4 options')
        if type(row) not in (list,tuple) or len(row)!=k:raise ValueError('cost rows must match zone count')
    for opts in options:
        if any(type(z) is not int or not 0<=z<k for z in opts):raise ValueError('zone options must be nonbool indices inside zone range')
        if len(set(opts))!=len(opts):raise ValueError('cell options must be unique')
    if any(type(v) is not int or not 0<=v<=n for v in minimum_counts):raise ValueError('minimum counts must be nonbool integers inside cell range')
    if any(type(v) is not int or not 0<=v<=1000000 for row in costs for v in row):raise ValueError('costs must be nonbool integers zero through 1000000')
    for pairs,limit in ((adjacency,n),(forbidden_pairs,k)):
        for pair in pairs:
            if type(pair) not in (list,tuple) or len(pair)!=2:raise ValueError('pairs must contain two indices')
            if any(type(v) is not int or not 0<=v<limit for v in pair):raise ValueError('pair indices must be nonbool integers inside corresponding range')
    blocked={tuple(sorted(pair)) for pair in forbidden_pairs};best=None;feasible=0
    for zones in product(*options):
        counts=[zones.count(z) for z in range(k)]
        if any(a<b for a,b in zip(counts,minimum_counts)):continue
        if any(tuple(sorted((zones[a],zones[b]))) in blocked for a,b in adjacency):continue
        feasible+=1;cost=sum(costs[i][z] for i,z in enumerate(zones))
        if best is None or cost<best[0]:best=(cost,zones,counts)
    if best is None:raise ValueError('no landscape satisfies zone constraints')
    cost,zones,counts=best
    return {'zones':list(zones),'zone_counts':counts,'cost':cost,'feasible_count':feasible,'ecology_validated':False}
