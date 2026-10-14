"""Row536 Data Warehouse Design: supplied star-schema referential validation.
Dimension keys map labels (integer codes); facts (key,measure) aggregate by
label, allowing multiple dimension keys with same label. Caps32dimensions,
64facts,32bit magnitude nonbool integers. NOT_CLAIMED: real warehouse design,
physical storage, SQL execution, analytics accuracy or external writes.
"""


def star_rollup(dimensions,facts):
    if type(dimensions) not in (list,tuple) or type(facts) not in (list,tuple):raise TypeError('inputs must be lists or tuples')
    if not 1<=len(dimensions)<=32 or len(facts)>64:raise ValueError('dimension cap is 32 and fact cap is 64')
    if any(type(row) not in (list,tuple) or len(row)!=2 for row in [*dimensions,*facts]):raise ValueError('records must contain exactly two cells')
    if any(type(v) is not int or v.bit_length()>32 for row in [*dimensions,*facts] for v in row):raise ValueError('cells must be nonbool 32-bit magnitude integers')
    lookup={}
    for key,label in dimensions:
        if key in lookup:raise ValueError('dimension keys must be unique')
        lookup[key]=label
    totals={};counts={}
    for key,value in facts:
        if key not in lookup:raise ValueError('fact key must reference dimension')
        label=lookup[key];totals[label]=totals.get(label,0)+value;counts[label]=counts.get(label,0)+1
    return {'label_rollups':[[label,counts[label],totals[label]] for label in sorted(totals)],'warehouse_created':False}
