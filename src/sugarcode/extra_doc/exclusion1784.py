"""Doc row1784 Social Exclusion: PARTIAL supplied service access matrix.

Services exact list1..20 unique valid labels; records exact list1..100 tuples
(id,accessible), unique IDs, accessible exact list0..20 unique known services.
Labels exact nonblank str1..80. Return missing services per record, records with
no supplied access and fully covered records. No exclusion or identity inference.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit_access(services,records):
    if type(services) is not list or not 1<=len(services)<=20 or any(not _label(x) for x in services) or len(set(services))!=len(services):raise ValueError('services must be an exact list of 1..20 unique valid labels')
    if type(records) is not list or not 1<=len(records)<=100:raise ValueError('records must be an exact list with 1..100 entries')
    ids=set()
    for row in records:
        if type(row) is not tuple or len(row)!=2:raise ValueError('record must be an id accessible tuple')
        n,access=row
        if not _label(n) or n in ids:raise ValueError('record IDs must be unique valid labels')
        ids.add(n)
        if type(access) is not list or len(access)>20 or any(not _label(x) or x not in services for x in access) or len(set(access))!=len(access):raise ValueError('accessible must be an exact list of 0..20 unique known service labels')
    return {'missing':[(n,[s for s in services if s not in access]) for n,access in records],'no_access':[n for n,access in records if not access],'full_access':[n for n,access in records if len(access)==len(services)],'claim':'PARTIAL','exclusion_inferred':False}
