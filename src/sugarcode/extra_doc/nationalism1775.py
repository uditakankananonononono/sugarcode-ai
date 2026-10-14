"""Doc row1775 Nationalism: PARTIAL supplied symbol-tag occurrence ledger.

Symbols exact list1..20 unique valid labels. Documents exact list1..100 tuples
(id,tags), unique IDs, tags exact list0..100 known symbol labels; repetitions
count as occurrences. Labels exact nonblank str1..80. Return occurrences and
number of documents containing each symbol. No ideology, nationality or identity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def count_symbols(symbols,documents):
    if type(symbols) is not list or not 1<=len(symbols)<=20 or any(not _label(x) for x in symbols) or len(set(symbols))!=len(symbols):raise ValueError('symbols must be an exact list of 1..20 unique valid labels')
    if type(documents) is not list or not 1<=len(documents)<=100:raise ValueError('documents must be an exact list with 1..100 entries')
    ids=set()
    for row in documents:
        if type(row) is not tuple or len(row)!=2:raise ValueError('document must be an id tags tuple')
        n,tags=row
        if not _label(n) or n in ids:raise ValueError('document IDs must be unique valid labels')
        ids.add(n)
        if type(tags) is not list or len(tags)>100 or any(not _label(x) or x not in symbols for x in tags):raise ValueError('tags must be an exact list of 0..100 known symbol labels')
    return {'counts':[(s,sum(tags.count(s) for n,tags in documents),sum(s in tags for n,tags in documents)) for s in symbols],'claim':'PARTIAL','ideology_inferred':False}
