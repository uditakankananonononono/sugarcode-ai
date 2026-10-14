"""Doc row1749 Hermeneutics: PARTIAL supplied interpretation-evidence links.

Passages exact list1..100 unique labels. Interpretations exact list1..20 tuples
(id,passage_refs), unique IDs, refs exact list1..100 unique known passage labels.
All labels exact nonblank str1..80. Return passage-to-interpretation links,
unreferenced passages and interpretation pairs sharing evidence. No endorsement
of interpretations, meaning, historical truth or hermeneutic validity.
"""
from itertools import combinations


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_links(passages,interpretations):
    if type(passages) is not list or not 1<=len(passages)<=100 or any(not _label(x) for x in passages) or len(set(passages))!=len(passages):raise ValueError('passages must be an exact list of 1..100 unique valid labels')
    if type(interpretations) is not list or not 1<=len(interpretations)<=20:raise ValueError('interpretations must be an exact list with 1..20 entries')
    ids=set()
    for row in interpretations:
        if type(row) is not tuple or len(row)!=2:raise ValueError('interpretation must be an id passage_refs tuple')
        name,refs=row
        if not _label(name) or name in ids:raise ValueError('interpretation IDs must be unique valid labels')
        ids.add(name)
        if type(refs) is not list or not 1<=len(refs)<=100 or any(not _label(x) or x not in passages for x in refs) or len(set(refs))!=len(refs):raise ValueError('refs must be an exact list of 1..100 unique known passage labels')
    links=[(p,[n for n,refs in interpretations if p in refs]) for p in passages]
    shared=[(a,b,sorted(set(ar)&set(br))) for (a,ar),(b,br) in combinations(interpretations,2) if set(ar)&set(br)]
    return {'links':links,'unreferenced':[p for p,names in links if not names],'shared_evidence':shared,'claim':'PARTIAL','interpretations_validated':False}
