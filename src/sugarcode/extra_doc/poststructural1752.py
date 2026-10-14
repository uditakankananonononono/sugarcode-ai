"""Doc row1752 Post-Structuralism: PARTIAL supplied reading disagreement ledger.

Readings exact list2..20 (id,assignments), unique valid IDs; assignments exact list
0..100 unique (term,meaning) tuples by term. Labels exact nonblank str1..80.
Return terms whose supplied meanings disagree and missing-reading coverage. No
inferred deconstruction, ideology, author intent or post-structuralist validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def compare_readings(readings):
    if type(readings) is not list or not 2<=len(readings)<=20:raise ValueError('readings must be an exact list with 2..20 entries')
    ids=set()
    for row in readings:
        if type(row) is not tuple or len(row)!=2:raise ValueError('reading must be an id assignments tuple')
        name,assignments=row
        if not _label(name) or name in ids:raise ValueError('reading IDs must be unique valid labels')
        ids.add(name)
        if type(assignments) is not list or len(assignments)>100:raise ValueError('assignments must be an exact list with 0..100 entries')
        terms=set()
        for pair in assignments:
            if type(pair) is not tuple or len(pair)!=2:raise ValueError('assignment must be a term meaning tuple')
            term,meaning=pair
            if not _label(term) or not _label(meaning) or term in terms:raise ValueError('assignment labels must be valid with unique terms')
            terms.add(term)
    terms=sorted({t for n,aa in readings for t,m in aa})
    disagreements=[];missing=[]
    for term in terms:
        assigned=[(n,m) for n,aa in readings for t,m in aa if t==term]
        if len({m for n,m in assigned})>1:disagreements.append((term,assigned))
        absent=[n for n,aa in readings if all(t!=term for t,m in aa)]
        if absent:missing.append((term,absent))
    return {'disagreements':disagreements,'missing':missing,'claim':'PARTIAL','interpretation_validated':False}
