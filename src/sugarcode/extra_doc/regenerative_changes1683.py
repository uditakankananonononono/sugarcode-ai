"""Regenerative Agriculture.

PARTIAL: caller before/after indicator changes only, not regenerative
agriculture, soil recovery, carbon sequestration or farming recommendations.
Caller indicators are abstract, not verified environmental measurements.
"""
from fractions import Fraction
SCOPE='caller before-after indicator changes only; no regenerative agriculture claims'


def changes(rows):
    """Exactlist/tuple1..64 triples(label,before,after);unique printable Unicode
    exactstr labels1..40;exactint values0..1000000. Sorted(label,after-before,
    change/before or None at zero before),strictly increased labels,total change.
    Mixedrows accepted;increased indicator is not inferred to be beneficial.
    No units,causality,soil improvement,carbon or ecosystem outcomes inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,before,after=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(before) is not int or type(after) is not int or not 0<=before<=1000000 or not 0<=after<=1000000:raise ValueError('values must be exactint0..1000000')
        delta=after-before;parsed.append((label,delta,Fraction(delta,before) if before else None))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'changes':result,'increased':tuple(row[0] for row in result if row[1]>0),'total_change':sum(row[1] for row in result),'scope':SCOPE}
