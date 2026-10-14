"""Row 305 Orchestration: exact instrument-to-part assignment.

Assigns distinct supplied instruments to supplied part pitch ranges within
instrument ranges, minimizing supplied compatibility costs. Returns first
lexicographic instrument tuple on cost ties; up to eight instruments/parts.
NOT_CLAIMED: timbral aesthetic quality, actual score engraving, extended
techniques, audio rendering, musical realism or autonomous publication.
"""
from itertools import permutations


def assign_instruments(parts,instruments,costs):
    if any(type(v) not in (list,tuple) for v in (parts,instruments,costs)):
        raise TypeError('inputs must be lists or tuples')
    p=len(parts);n=len(instruments)
    if not 1<=p<=n<=8:raise ValueError('counts must satisfy 1 <= parts <= instruments <= 8')
    for bounds in list(parts)+list(instruments):
        if type(bounds) not in (list,tuple) or len(bounds)!=2:
            raise ValueError('ranges must contain lower and upper MIDI pitches')
    if len(costs)!=p or any(type(row) not in (list,tuple) or len(row)!=n for row in costs):
        raise ValueError('cost matrix must match parts and instruments')
    for low,high in list(parts)+list(instruments):
        if type(low) is not int or type(high) is not int or not 0<=low<=high<=127:
            raise ValueError('ranges must be ordered nonbool MIDI integers zero through 127')
    if any(type(v) is not int or not 0<=v<=1000000 for row in costs for v in row):
        raise ValueError('costs must be nonbool integers between zero and 1000000')
    best=None;feasible=0
    for assignment in permutations(range(n),p):
        if any(not instruments[j][0]<=parts[i][0]<=parts[i][1]<=instruments[j][1] for i,j in enumerate(assignment)):
            continue
        feasible+=1;cost=sum(costs[i][j] for i,j in enumerate(assignment))
        if best is None or cost<best[0]:best=(cost,assignment)
    if best is None:raise ValueError('no range-compatible distinct assignment exists')
    cost,assignment=best
    return {'instrument_indices':list(assignment),'compatibility_cost':cost,
            'feasible_assignment_count':feasible,'timbral_quality_validated':False}
