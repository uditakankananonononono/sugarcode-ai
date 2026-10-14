"""Row535 ETL Pipeline Design: pure supplied integer-table filter/project/group.

Extract supplied rows, filter selected column>=threshold,project selected
columns, group first projected column summing second. Preserve selected rows.
Caps64rows/16cols,32bit magnitude cells/threshold; exact unbounded totals.
NOT_CLAIMED: external ETL/database movement, durable loading, real schema,
scheduling, production pipeline, credentials or live-system edits.
"""


def etl_table(rows,filter_column,threshold,projection):
    if type(rows) not in (list,tuple) or type(projection) not in (list,tuple):raise TypeError('inputs must be lists or tuples')
    if not 1<=len(rows)<=64:raise ValueError('row count must be between 1 and 64')
    if any(type(row) not in (list,tuple) or not 1<=len(row)<=16 for row in rows):raise ValueError('rows must contain 1 through 16 cells')
    n=len(rows[0])
    if any(len(row)!=n for row in rows):raise ValueError('rows must be rectangular')
    if len(projection)!=2:raise ValueError('projection must contain exactly two indices')
    if any(type(i) is not int or not 0<=i<n for i in [filter_column,*projection]):raise ValueError('columns must be nonbool valid indices')
    if any(type(v) is not int or v.bit_length()>32 for row in rows for v in row) or type(threshold) is not int or threshold.bit_length()>32:raise ValueError('cells and threshold must be nonbool 32-bit magnitude integers')
    extracted=[list(row) for row in rows if row[filter_column]>=threshold]
    projected=[[row[i] for i in projection] for row in extracted];groups={}
    for key,value in projected:groups[key]=groups.get(key,0)+value
    return {'selected_rows':extracted,'projected_rows':projected,'group_totals':[[key,value] for key,value in sorted(groups.items())],'external_load_performed':False}
