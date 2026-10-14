"""Doc row1028 Missing Data Imputation: PARTIAL exact column mean fill.

Input exact rectangular list1..50 rows, exact list1..20 columns, cells None or
nonbool int-1000..1000. Compute each mean from observed cells only; all-missing
columns remain None. Output each numeric cell as normalized rational pair and
None otherwise, plus filled(row,col) indexes. No missingness assumptions or
validity of resulting analysis claimed. No mutation of supplied data.
"""
from fractions import Fraction


def fill(table):
    if type(table) is not list or not 1<=len(table)<=50:
        raise ValueError('table must be an exact list with 1..50 rows')
    width=None
    for row in table:
        if type(row) is not list or not 1<=len(row)<=20:
            raise ValueError('rows must be exact lists with 1..20 cells')
        if width is None:width=len(row)
        if len(row)!=width:raise ValueError('rows must have equal width')
        if any(x is not None and (type(x) is not int or not -1000<=x<=1000) for x in row):
            raise ValueError('cells must be None or integers in -1000..1000')
    means=[]
    for j in range(width):
        observed=[row[j] for row in table if row[j] is not None]
        means.append(Fraction(sum(observed),len(observed)) if observed else None)
    output=[];filled=[]
    for i,row in enumerate(table):
        result=[]
        for j,x in enumerate(row):
            value=means[j] if x is None else Fraction(x)
            if x is None and value is not None:filled.append((i,j))
            result.append(None if value is None else (value.numerator,value.denominator))
        output.append(result)
    return {'table':output,'filled':filled,'claim':'PARTIAL','missingness_validated':False}
