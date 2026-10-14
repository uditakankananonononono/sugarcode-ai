"""Doc row1755 Queer Theory: PARTIAL supplied norm/category annotation ledger.

Categories exact list2..20 unique valid labels; records exact list1..100 tuples
(id,tags), unique IDs, tags exact list0..20 unique known category labels. Labels
exact nonblank str1..80. Return supplied untagged, single-tag and multi-tag record
IDs and unused categories. No inferred orientation, gender, identity, normativity
or queer theory validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_tags(categories,records):
    if type(categories) is not list or not 2<=len(categories)<=20 or any(not _label(x) for x in categories) or len(set(categories))!=len(categories):raise ValueError('categories must be an exact list of 2..20 unique valid labels')
    if type(records) is not list or not 1<=len(records)<=100:raise ValueError('records must be an exact list with 1..100 entries')
    ids=set()
    for row in records:
        if type(row) is not tuple or len(row)!=2:raise ValueError('record must be an id tags tuple')
        name,tags=row
        if not _label(name) or name in ids:raise ValueError('record IDs must be unique valid labels')
        ids.add(name)
        if type(tags) is not list or len(tags)>20 or any(not _label(x) or x not in categories for x in tags) or len(set(tags))!=len(tags):raise ValueError('tags must be an exact list of 0..20 unique known category labels')
    return {'untagged':[n for n,ts in records if not ts],'single_tag':[n for n,ts in records if len(ts)==1],'multi_tag':[n for n,ts in records if len(ts)>1],'unused_categories':[c for c in categories if all(c not in ts for n,ts in records)],'claim':'PARTIAL','identity_inferred':False,'theory_validated':False}
