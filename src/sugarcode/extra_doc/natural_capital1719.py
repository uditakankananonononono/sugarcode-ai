"""Doc row1719 Natural Capitalism: PARTIAL supplied resource-intensity fixture.

Rows exact list1..50 unique tuples(id,output,resource), exact nonbool ints output
1..10000/resource0..10000. IDs nonblank exact str<=80. Report exact resource per
output and rank ascending intensity then ID, totals and overall intensity.
No economic, ecological, financial or actual sustainability assessment claimed.
"""
from fractions import Fraction


def compare(rows):
    if type(rows) is not list or not 1<=len(rows)<=50:
        raise ValueError('rows must be an exact list with 1..50 entries')
    ids=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('row must be an id output resource tuple')
        name,output,resource=row
        if type(name) is not str or not 1<=len(name)<=80 or not name.strip() or name in ids:
            raise ValueError('IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(name)
        if type(output) is not int or not 1<=output<=10000:
            raise ValueError('output must be an integer in 1..10000')
        if type(resource) is not int or not 0<=resource<=10000:
            raise ValueError('resource must be an integer in 0..10000')
    values=sorted([(n,Fraction(r,o)) for n,o,r in rows],key=lambda x:(x[1],x[0]))
    output=sum(o for _,o,r in rows);resource=sum(r for _,o,r in rows);overall=Fraction(resource,output)
    return {'ranking':[(n,(v.numerator,v.denominator)) for n,v in values],'output':output,'resource':resource,
            'overall':(overall.numerator,overall.denominator),'claim':'PARTIAL','sustainability_validated':False}
