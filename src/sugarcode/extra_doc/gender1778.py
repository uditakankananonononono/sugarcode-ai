"""Doc row1778 Gender Relations: PARTIAL supplied category task-allocation ledger.

Categories exact list2..20 unique valid labels; tasks exact list1..100 tuples
(id,category,units), unique task IDs, category known label, units exact int0..1000.
Labels exact nonblank str1..80. Return category task counts and allocated units.
No inference of gender, identity, discrimination, fairness or social relationships.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_allocations(categories,tasks):
    if type(categories) is not list or not 2<=len(categories)<=20 or any(not _label(x) for x in categories) or len(set(categories))!=len(categories):raise ValueError('categories must be an exact list of 2..20 unique valid labels')
    if type(tasks) is not list or not 1<=len(tasks)<=100:raise ValueError('tasks must be an exact list with 1..100 entries')
    ids=set()
    for row in tasks:
        if type(row) is not tuple or len(row)!=3:raise ValueError('task must be an id category units tuple')
        n,c,u=row
        if not _label(n) or n in ids:raise ValueError('task IDs must be unique valid labels')
        ids.add(n)
        if not _label(c) or c not in categories:raise ValueError('category must be a known valid label')
        if type(u) is not int or not 0<=u<=1000:raise ValueError('units must be an integer in 0..1000')
    return {'allocations':[(c,sum(cat==c for n,cat,u in tasks),sum(u for n,cat,u in tasks if cat==c)) for c in categories],'claim':'PARTIAL','gender_inferred':False,'fairness_validated':False}
