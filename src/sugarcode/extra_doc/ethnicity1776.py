"""Doc row1776 Ethnicity: PARTIAL supplied self-label frequency ledger.

Records exact list1..100 (id,labels) tuples; unique valid IDs; labels exact list
0..20 unique labels. Labels exact nonblank str1..80. Return frequencies, unlabelled
IDs and multi-label IDs. No inference of ethnicity, ancestry, identity or culture.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def count_labels(records):
    if type(records) is not list or not 1<=len(records)<=100:raise ValueError('records must be an exact list with 1..100 entries')
    ids=set()
    for row in records:
        if type(row) is not tuple or len(row)!=2:raise ValueError('record must be an id labels tuple')
        n,labels=row
        if not _label(n) or n in ids:raise ValueError('record IDs must be unique valid labels')
        ids.add(n)
        if type(labels) is not list or len(labels)>20 or any(not _label(x) for x in labels) or len(set(labels))!=len(labels):raise ValueError('labels must be an exact list of 0..20 unique valid labels')
    labels=sorted({x for n,ls in records for x in ls})
    return {'frequencies':[(x,sum(x in ls for n,ls in records)) for x in labels],'unlabelled':[n for n,ls in records if not ls],'multiple':[n for n,ls in records if len(ls)>1],'claim':'PARTIAL','ethnicity_inferred':False}
