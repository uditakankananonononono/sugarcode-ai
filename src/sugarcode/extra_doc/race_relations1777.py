"""Doc row1777 Race Relations: PARTIAL supplied category contact ledger.

Categories exact list2..20 unique valid labels; contacts exact list0..100 tuples
(source,target,count), endpoints known valid labels, count exact int0..1000.
Repeated and self contacts allowed; return ordered aggregate nonzero category
pair counts and total same/different-label counts. No race, prejudice or social
relationship inference. Labels exact nonblank str1..80.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def count_contacts(categories,contacts):
    if type(categories) is not list or not 2<=len(categories)<=20 or any(not _label(x) for x in categories) or len(set(categories))!=len(categories):raise ValueError('categories must be an exact list of 2..20 unique valid labels')
    if type(contacts) is not list or len(contacts)>100:raise ValueError('contacts must be an exact list with 0..100 entries')
    counts={}
    for row in contacts:
        if type(row) is not tuple or len(row)!=3:raise ValueError('contact must be a source target count tuple')
        a,b,n=row
        if not _label(a) or not _label(b) or a not in categories or b not in categories:raise ValueError('endpoints must be known valid labels')
        if type(n) is not int or not 0<=n<=1000:raise ValueError('count must be an integer in 0..1000')
        counts[(a,b)]=counts.get((a,b),0)+n
    pairs=[(a,b,counts.get((a,b),0)) for a in categories for b in categories if counts.get((a,b),0)>0]
    return {'pairs':pairs,'same':sum(n for a,b,n in contacts if a==b),'different':sum(n for a,b,n in contacts if a!=b),'claim':'PARTIAL','race_inferred':False}
