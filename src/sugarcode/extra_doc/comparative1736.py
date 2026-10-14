"""Doc row1736 Comparative Research: PARTIAL supplied binary feature comparison.

Cases exact list2..50 tuples(id,feature-list), unique valid IDs; features exact
list0..20 unique nonblank exact str<=80. Output all-case common features sorted,
and unique-to-case features sorted in case input order. No causal/comparative
research validity or inference beyond exact set membership claimed.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def compare(cases):
    if type(cases) is not list or not 2<=len(cases)<=50:
        raise ValueError('cases must be an exact list with 2..50 entries')
    ids=set()
    for row in cases:
        if type(row) is not tuple or len(row)!=2:
            raise ValueError('case must be an id features tuple')
        name,features=row
        if not _label(name) or name in ids:raise ValueError('case IDs must be unique valid labels')
        ids.add(name)
        if type(features) is not list or len(features)>20 or any(not _label(x) for x in features) or len(set(features))!=len(features):
            raise ValueError('features must be an exact list of 0..20 unique valid labels')
    sets=[set(f) for n,f in cases];common=set.intersection(*sets);unique=[]
    for i,(name,features) in enumerate(cases):
        others=set().union(*(s for j,s in enumerate(sets) if i!=j));unique.append((name,sorted(sets[i]-others)))
    return {'common':sorted(common),'unique':unique,'claim':'PARTIAL','research_validated':False}
