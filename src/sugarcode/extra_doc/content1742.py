"""Doc row1742 Content Analysis: PARTIAL supplied manual-code frequency audit.

Categories exact list2..20 unique nonblank exact str1..80. Units exact list1..100
unique (id,codes) tuples; codes exact list0..20 unique category labels; IDs same
label contract. Counts units with each category and pair co-occurrences, in
supplied category order. No automatic coding, coder reliability or interpretation.
"""
from itertools import combinations


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def count_codes(categories,units):
    if type(categories) is not list or not 2<=len(categories)<=20 or any(not _label(x) for x in categories) or len(set(categories))!=len(categories):
        raise ValueError('categories must be an exact list of 2..20 unique valid labels')
    if type(units) is not list or not 1<=len(units)<=100:
        raise ValueError('units must be an exact list with 1..100 entries')
    ids=set()
    for row in units:
        if type(row) is not tuple or len(row)!=2:raise ValueError('unit must be an id codes tuple')
        name,codes=row
        if not _label(name) or name in ids:raise ValueError('unit IDs must be unique valid labels')
        ids.add(name)
        if type(codes) is not list or len(codes)>20 or any(not _label(x) or x not in categories for x in codes) or len(set(codes))!=len(codes):
            raise ValueError('codes must be an exact list of 0..20 unique category labels')
    counts=[(c,sum(c in codes for n,codes in units)) for c in categories]
    pairs=[(a,b,sum(a in codes and b in codes for n,codes in units)) for a,b in combinations(categories,2)]
    return {'counts':counts,'cooccurrences':pairs,'claim':'PARTIAL','coding_validated':False}
