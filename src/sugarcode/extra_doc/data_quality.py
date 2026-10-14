"""Row534 Data Quality: supplied integer-table completeness/uniqueness checks.

None cells count missing; duplicate rows and duplicate nonmissing key-column
values identified separately. Exact completeness fraction over all cells.
Caps64rows/16columns/32bit magnitude integers or None. NOT_CLAIMED: accuracy,
semantic correctness, real data quality, external database or automatic fixes.
"""
from fractions import Fraction


def quality_report(rows,key_column):
    if type(rows) not in (list,tuple):raise TypeError('rows must be a list or tuple')
    if not 1<=len(rows)<=64:raise ValueError('row count must be between 1 and 64')
    if any(type(row) not in (list,tuple) or not 1<=len(row)<=16 for row in rows):raise ValueError('rows must contain 1 through 16 cells')
    n=len(rows[0])
    if any(len(row)!=n for row in rows):raise ValueError('rows must be rectangular')
    if type(key_column) is not int or not 0<=key_column<n:raise ValueError('key column must be nonbool valid index')
    if any(v is not None and (type(v) is not int or v.bit_length()>32) for row in rows for v in row):raise ValueError('cells must be None or nonbool 32-bit magnitude integers')
    missing=[[i,j] for i,row in enumerate(rows) for j,v in enumerate(row) if v is None];seen={};keys={};duplicates=[];duplicate_keys=[]
    for i,row in enumerate(rows):
        record=tuple(row)
        if record in seen:duplicates.append([seen[record],i])
        else:seen[record]=i
        key=row[key_column]
        if key is not None:
            if key in keys:duplicate_keys.append([keys[key],i])
            else:keys[key]=i
    return {'missing_cells':missing,'duplicate_rows':duplicates,'duplicate_keys':duplicate_keys,
            'completeness':Fraction(len(rows)*n-len(missing),len(rows)*n),'accuracy_validated':False}
