"""Doc row1760 Organizational Analysis: PARTIAL supplied reporting-tree audit.

Members exact list1..100 tuples(id,manager), unique labels exact nonblank str1..80;
manager None or known distinct member label. Exactly one root; cycles forbidden.
Return reporting depths and direct reports sorted for members in input order. No
real organization hierarchy, effectiveness or personnel inference.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_structure(members):
    if type(members) is not list or not 1<=len(members)<=100:raise ValueError('members must be an exact list with 1..100 entries')
    ids=set()
    for row in members:
        if type(row) is not tuple or len(row)!=2:raise ValueError('member must be an id manager tuple')
        name,manager=row
        if not _label(name) or name in ids:raise ValueError('member IDs must be unique valid labels')
        ids.add(name)
        if manager is not None and not _label(manager):raise ValueError('manager must be None or a valid label')
    parents=dict(members)
    if any(p is not None and (p not in ids or p==n) for n,p in members):raise ValueError('managers must be known distinct members')
    roots=[n for n,p in members if p is None]
    if len(roots)!=1:raise ValueError('exactly one root is required')
    depths=[]
    for name,parent in members:
        seen={name};depth=0
        while parent is not None:
            if parent in seen:raise ValueError('reporting cycles are forbidden')
            seen.add(parent);depth+=1;parent=parents[parent]
        depths.append((name,depth))
    reports=[(n,sorted(a for a,p in members if p==n)) for n,p in members]
    return {'root':roots[0],'depths':depths,'direct_reports':reports,'claim':'PARTIAL','organization_validated':False}
