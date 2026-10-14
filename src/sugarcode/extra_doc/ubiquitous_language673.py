"""Doc row673 Ubiquitous Language: PARTIAL exact glossary consistency audit.

Entries exact list0..100 tuples(context,term,definition). Each string nonblank
exact str<=120. Repeated context-term is invalid. Report terms with conflicting
exact definitions across contexts, terms with a shared exact definition across
multiple contexts, and definitions mapped to multiple terms. All groups lexically
sorted; no normalization, semantic equivalence or real shared language claim.
"""


def audit(entries):
    if type(entries) is not list or len(entries)>100:
        raise ValueError('entries must be an exact list with 0..100 entries')
    seen=set()
    for row in entries:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('entry must be a context, term, definition tuple')
        if any(type(x) is not str or not 1<=len(x)<=120 or not x.strip() for x in row):
            raise ValueError('fields must be nonblank exact strings of 1..120 characters')
        key=row[:2]
        if key in seen:raise ValueError('context-term pairs must be unique')
        seen.add(key)
    terms,definitions={},{}
    for context,term,definition in entries:
        terms.setdefault(term,[]).append((context,definition))
        definitions.setdefault(definition,set()).add(term)
    conflicts,shared=[],[]
    for term,rows in sorted(terms.items()):
        distinct={d for _,d in rows}
        if len(distinct)>1:conflicts.append((term,sorted(rows)))
        elif len(rows)>1:shared.append((term,next(iter(distinct)),sorted(c for c,_ in rows)))
    return {'conflicts':conflicts,'shared':shared,
            'definition_aliases':[(d,sorted(t)) for d,t in sorted(definitions.items()) if len(t)>1],
            'claim':'PARTIAL','semantic_equivalence_validated':False}
