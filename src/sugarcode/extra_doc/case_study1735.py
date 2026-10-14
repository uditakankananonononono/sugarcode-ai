"""Doc row1735 Case Study Design: PARTIAL supplied evidence triangulation fixture.

Claims exact list1..20 unique valid labels. Evidence exact list0..100 tuples
(id,claim,source), distinct IDs; nonblank exact str<=80 labels. Return per claim
unique source count and sorted sources, claims with fewer than2 sources and
unknown evidence IDs. No case truth, source independence or research-validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit(claims,evidence):
    if type(claims) is not list or not 1<=len(claims)<=20:
        raise ValueError('claims must be an exact list with 1..20 entries')
    if any(not _label(x) for x in claims) or len(set(claims))!=len(claims):
        raise ValueError('claims must be unique valid labels')
    if type(evidence) is not list or len(evidence)>100:
        raise ValueError('evidence must be an exact list with 0..100 entries')
    ids=set()
    for row in evidence:
        if type(row) is not tuple or len(row)!=3 or any(not _label(x) for x in row):
            raise ValueError('evidence must be valid id claim source tuples')
        if row[0] in ids:raise ValueError('evidence IDs must be unique')
        ids.add(row[0])
    sources={c:set() for c in claims};unknown=[]
    for name,c,s in evidence:
        if c in sources:sources[c].add(s)
        else:unknown.append(name)
    return {'sources':[(c,len(sources[c]),sorted(sources[c])) for c in claims],
            'under_triangulated':[c for c in claims if len(sources[c])<2],'unknown':unknown,
            'claim':'PARTIAL','truth_validated':False}
