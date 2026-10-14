"""Doc row1748 Phenomenology: PARTIAL supplied participant-description ledger.

Descriptions exact list1..100 (participant,descriptors) tuples, unique participant
IDs; descriptors exact list0..20 unique labels. Labels exact nonblank str1..80.
Return each descriptor's participants and supplied universal descriptors. No
inferred lived experience, essence, diagnosis, identity or phenomenological validity.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def summarize(descriptions):
    if type(descriptions) is not list or not 1<=len(descriptions)<=100:raise ValueError('descriptions must be an exact list with 1..100 entries')
    ids=set()
    for row in descriptions:
        if type(row) is not tuple or len(row)!=2:raise ValueError('description must be a participant descriptors tuple')
        name,descriptors=row
        if not _label(name) or name in ids:raise ValueError('participant IDs must be unique valid labels')
        ids.add(name)
        if type(descriptors) is not list or len(descriptors)>20 or any(not _label(x) for x in descriptors) or len(set(descriptors))!=len(descriptors):raise ValueError('descriptors must be an exact list of 0..20 unique valid labels')
    labels=sorted({x for n,ds in descriptions for x in ds})
    membership=[(x,sorted(n for n,ds in descriptions if x in ds)) for x in labels]
    universal=[x for x,people in membership if len(people)==len(descriptions)]
    return {'descriptor_participants':membership,'universal':universal,'claim':'PARTIAL','experience_validated':False}
