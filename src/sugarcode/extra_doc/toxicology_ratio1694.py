"""Toxicology.

PARTIAL: caller value/reference ratios only, not toxicology, toxicity testing,
dose-response modeling, diagnosis, poisoning triage or treatment advice.
Caller references are abstract, not safe doses or toxicological thresholds.
"""
from fractions import Fraction
SCOPE='caller value-reference ratios only; no toxicology or safety claims'


def exceedances(rows):
    """Exactlist/tuple1..64 triples(label,value,limit);unique printable Unicode
    exactstr labels1..40;exactint value0..1000000,limit1..1000000. Sorted
    (label,value/limit,max(value-limit,0)),strictly exceeding labels and total
    excess. Mixedrows accepted;no units,site history or safe/unsafe inference.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,value,limit=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(value) is not int or type(limit) is not int or not 0<=value<=1000000 or not 1<=limit<=1000000:raise ValueError('value must be exactint0..1000000 and limit exactint1..1000000')
        parsed.append((label,Fraction(value,limit),max(value-limit,0)))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'exceedances':result,'above':tuple(row[0] for row in result if row[1]>1),'total_excess':sum(row[2] for row in result),'scope':SCOPE}
