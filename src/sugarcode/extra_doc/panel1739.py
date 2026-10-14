"""Doc row1739 Panel Studies: PARTIAL supplied wave membership/attrition audit.

Waves exact list2..20 tuples(id,members), unique valid IDs, members exact list
0..100 unique nonblank exact str<=80. Return retained/lost/added members for each
successive pair sorted, plus members present in every wave. No real attrition
reason, representative panel, longitudinal causal validity or contact effects.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit(waves):
    if type(waves) is not list or not 2<=len(waves)<=20:
        raise ValueError('waves must be an exact list with 2..20 entries')
    ids=set()
    for row in waves:
        if type(row) is not tuple or len(row)!=2:raise ValueError('wave must be an id members tuple')
        name,members=row
        if not _label(name) or name in ids:raise ValueError('wave IDs must be unique valid labels')
        ids.add(name)
        if type(members) is not list or len(members)>100 or any(not _label(x) for x in members) or len(set(members))!=len(members):
            raise ValueError('members must be an exact list of 0..100 unique valid labels')
    changes=[]
    for (a,left),(b,right) in zip(waves,waves[1:]):
        l,r=set(left),set(right);changes.append((a,b,sorted(l&r),sorted(l-r),sorted(r-l)))
    stable=set.intersection(*(set(m) for n,m in waves))
    return {'changes':changes,'stable':sorted(stable),'claim':'PARTIAL','panel_validated':False}
