"""Ecological Footprinting.

PARTIAL: caller demand/yield equivalent-area arithmetic only, not ecological
footprinting, biocapacity assessment, sustainability or environmental advice.
Caller factors are abstract, not verified yields or ecological inventories.
"""
from fractions import Fraction
SCOPE='caller demand-yield equivalent-area arithmetic only; no ecological footprint claims'


def areas(rows):
    """Exactlist/tuple1..64 triples(label,demand,yield);unique printable Unicode
    exactstr labels1..40;exactint demand0..1000000,yield1..1000000. Sorted
    (label,demand/yield),total equivalent area and zero-area labels.
    Mixedrows accepted;no physical units,equivalence factors,overshoot,land
    eligibility or actual resource footprint inferred from abstract ratios.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,demand,yield_value=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(demand) is not int or type(yield_value) is not int or not 0<=demand<=1000000 or not 1<=yield_value<=1000000:raise ValueError('demand must be exactint0..1000000 and yield exactint1..1000000')
        parsed.append((label,Fraction(demand,yield_value)))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'areas':result,'total_area':sum(value for label,value in result),'zero':tuple(label for label,value in result if value==0),'scope':SCOPE}
