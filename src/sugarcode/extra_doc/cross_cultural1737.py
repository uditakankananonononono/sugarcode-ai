"""Doc row1737 Cross-Cultural Research: PARTIAL supplied instrument coverage.

Requirements exact list1..20 unique valid labels. Groups exact list2..50 tuples
(id,item-list), unique IDs, items exact list0..20 unique labels; all labels
nonblank exact str<=80. Report missing requirements per group and intersection
of supplied items sorted. No cross-cultural equivalence, ethics or group traits.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit(requirements,groups):
    if type(requirements) is not list or not 1<=len(requirements)<=20:
        raise ValueError('requirements must be an exact list with 1..20 entries')
    if any(not _label(x) for x in requirements) or len(set(requirements))!=len(requirements):
        raise ValueError('requirements must be unique valid labels')
    if type(groups) is not list or not 2<=len(groups)<=50:
        raise ValueError('groups must be an exact list with 2..50 entries')
    ids=set()
    for row in groups:
        if type(row) is not tuple or len(row)!=2:raise ValueError('group must be an id items tuple')
        name,items=row
        if not _label(name) or name in ids:raise ValueError('group IDs must be unique valid labels')
        ids.add(name)
        if type(items) is not list or len(items)>20 or any(not _label(x) for x in items) or len(set(items))!=len(items):
            raise ValueError('items must be an exact list of 0..20 unique valid labels')
    shared=set.intersection(*(set(items) for n,items in groups))
    return {'missing':[(n,[r for r in requirements if r not in items]) for n,items in groups],
            'shared':sorted(shared),'claim':'PARTIAL','equivalence_validated':False}
