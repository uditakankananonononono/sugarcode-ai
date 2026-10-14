"""Doc row1750 Semiotics: PARTIAL supplied sign/meaning ambiguity ledger.

Signs exact list1..100 tuples(sign,meanings), unique sign IDs; meanings exact list
1..20 unique labels. Labels exact nonblank str1..80. Return supplied ambiguous
signs and meanings shared across signs. No inferred meaning, cultural sign system
or semiotic validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_signs(signs):
    if type(signs) is not list or not 1<=len(signs)<=100:raise ValueError('signs must be an exact list with 1..100 entries')
    ids=set()
    for row in signs:
        if type(row) is not tuple or len(row)!=2:raise ValueError('sign must be an id meanings tuple')
        name,meanings=row
        if not _label(name) or name in ids:raise ValueError('sign IDs must be unique valid labels')
        ids.add(name)
        if type(meanings) is not list or not 1<=len(meanings)<=20 or any(not _label(x) for x in meanings) or len(set(meanings))!=len(meanings):raise ValueError('meanings must be an exact list of 1..20 unique valid labels')
    labels=sorted({m for n,ms in signs for m in ms})
    shared=[(m,sorted(n for n,ms in signs if m in ms)) for m in labels if sum(m in ms for n,ms in signs)>1]
    ambiguous=[(n,sorted(ms)) for n,ms in signs if len(ms)>1]
    return {'ambiguous':ambiguous,'shared_meanings':shared,'claim':'PARTIAL','meaning_validated':False}
