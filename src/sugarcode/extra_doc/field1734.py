"""Doc row1734 Field Research: PARTIAL supplied visit-window conflict fixture.

Visits exact list0..50 tuples(id,site,start,end), unique IDs; nonblank exact
str<=80 labels, times exact nonbool int0..1440 and start<end. Half-open intervals;
report same-site overlap ID pairs in input pair order. No travel, actual visits,
permissions, ethics or field conditions claimed.
"""


def conflicts(visits):
    if type(visits) is not list or len(visits)>50:
        raise ValueError('visits must be an exact list with 0..50 entries')
    ids=set()
    for row in visits:
        if type(row) is not tuple or len(row)!=4:
            raise ValueError('visit must be an id site start end tuple')
        name,site,start,end=row
        if any(type(x) is not str or not 1<=len(x)<=80 or not x.strip() for x in (name,site)) or name in ids:
            raise ValueError('labels must be valid with unique visit IDs')
        ids.add(name)
        if type(start) is not int or type(end) is not int or not 0<=start<end<=1440:
            raise ValueError('times must be integers with 0<=start<end<=1440')
    overlaps=[]
    for i,(a,site,start,end) in enumerate(visits):
        for b,other,s,e in visits[i+1:]:
            if site==other and max(start,s)<min(end,e):overlaps.append((a,b))
    return {'overlaps':overlaps,'claim':'PARTIAL','field_conditions_validated':False}
