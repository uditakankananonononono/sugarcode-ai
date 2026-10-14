"""Doc row1779 Class Analysis: PARTIAL supplied ordered income-band ledger.

Thresholds exact list1..20 strictly increasing exact int1..1000. Records exact
list1..100 tuples(id,income), unique nonblank exact str1..80 IDs, income exact
int0..1000. Band index is count of thresholds<=income (lower bound inclusive).
Return record bands and each band's count in order. No class or status inference.
"""


def assign_bands(thresholds,records):
    if type(thresholds) is not list or not 1<=len(thresholds)<=20 or any(type(t) is not int or not 1<=t<=1000 for t in thresholds) or any(a>=b for a,b in zip(thresholds,thresholds[1:])):raise ValueError('thresholds must be an exact list of 1..20 strictly increasing integers in 1..1000')
    if type(records) is not list or not 1<=len(records)<=100:raise ValueError('records must be an exact list with 1..100 entries')
    ids=set()
    for row in records:
        if type(row) is not tuple or len(row)!=2:raise ValueError('record must be an id income tuple')
        n,income=row
        if type(n) is not str or not 1<=len(n)<=80 or not n.strip() or n in ids:raise ValueError('record IDs must be unique nonblank exact strings of 1..80 characters')
        ids.add(n)
        if type(income) is not int or not 0<=income<=1000:raise ValueError('income must be an integer in 0..1000')
    bands=[(n,sum(t<=income for t in thresholds)) for n,income in records]
    return {'bands':bands,'counts':[(i,sum(b==i for n,b in bands)) for i in range(len(thresholds)+1)],'claim':'PARTIAL','class_inferred':False}
