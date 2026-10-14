"""Doc row1753 Critical Theory: PARTIAL supplied critique/evidence coverage.

Evidence exact list1..100 unique labels; critiques exact list1..20 tuples(id,refs)
unique IDs; refs exact list0..100 unique known evidence labels. All labels exact
nonblank str1..80. Return unsupported critique IDs, unreferenced evidence and
per-evidence critique count. No normative judgment, oppression inference or theory.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_coverage(evidence,critiques):
    if type(evidence) is not list or not 1<=len(evidence)<=100 or any(not _label(x) for x in evidence) or len(set(evidence))!=len(evidence):raise ValueError('evidence must be an exact list of 1..100 unique valid labels')
    if type(critiques) is not list or not 1<=len(critiques)<=20:raise ValueError('critiques must be an exact list with 1..20 entries')
    ids=set()
    for row in critiques:
        if type(row) is not tuple or len(row)!=2:raise ValueError('critique must be an id refs tuple')
        name,refs=row
        if not _label(name) or name in ids:raise ValueError('critique IDs must be unique valid labels')
        ids.add(name)
        if type(refs) is not list or len(refs)>100 or any(not _label(x) or x not in evidence for x in refs) or len(set(refs))!=len(refs):raise ValueError('refs must be an exact list of 0..100 unique known evidence labels')
    counts=[(e,sum(e in refs for n,refs in critiques)) for e in evidence]
    return {'unsupported':[n for n,refs in critiques if not refs],'unused':[e for e,count in counts if count==0],'counts':counts,'claim':'PARTIAL','critique_validated':False}
