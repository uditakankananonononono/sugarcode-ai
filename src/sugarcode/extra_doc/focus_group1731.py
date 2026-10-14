"""Doc row1731 Focus Group Design: PARTIAL supplied group-size/category audit.

Participants exact list0..100 tuples(id,group,category), unique IDs, labels
nonblank exact str<=80. Minimum/maximum exact ints1<=min<=max<=20. Return group
sizes, out-of-bounds group IDs, categories represented by only one group (sorted
category/group pairs). No recruitment, discussion validity or representation.
"""


def audit(participants,minimum,maximum):
    if type(minimum) is not int or type(maximum) is not int or not 1<=minimum<=maximum<=20:
        raise ValueError('bounds must be integers with 1<=minimum<=maximum<=20')
    if type(participants) is not list or len(participants)>100:
        raise ValueError('participants must be an exact list with 0..100 entries')
    ids=set()
    for row in participants:
        if type(row) is not tuple or len(row)!=3 or any(type(x) is not str or not 1<=len(x)<=80 or not x.strip() for x in row):
            raise ValueError('participants must be valid id group category tuples')
        if row[0] in ids:raise ValueError('participant IDs must be unique')
        ids.add(row[0])
    groups={};categories={}
    for n,g,c in participants:
        groups[g]=groups.get(g,0)+1;categories.setdefault(c,set()).add(g)
    return {'sizes':sorted(groups.items()),'size_flags':[g for g,size in sorted(groups.items()) if size<minimum or size>maximum],
            'single_group_categories':[(c,next(iter(gs))) for c,gs in sorted(categories.items()) if len(gs)==1],
            'claim':'PARTIAL','representation_validated':False}
