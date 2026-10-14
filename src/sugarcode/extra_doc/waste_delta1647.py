"""Waste Reduction.

PARTIAL: caller baseline/current waste arithmetic only, not waste prevention,
verified measurements, environmental benefit or regulatory compliance.
Quantities are caller-defined units, not independently verified waste data.
"""
from fractions import Fraction
SCOPE='caller baseline-current arithmetic only; no verified waste reduction claims'


def reductions(rows):
    """Exactlist/tuple1..64 triples(label,baseline,current);unique printable
    Unicode exactstr labels1..40;exactint quantities0..1000000. Sorted output
    (label,baseline-current,delta/baseline or None when baseline zero),total
    delta and strictly increased labels. Negative delta means increase.
    Mixed row containers accepted; no units or policy thresholds inferred.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,baseline,current=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(baseline) is not int or type(current) is not int or not 0<=baseline<=1000000 or not 0<=current<=1000000:raise ValueError('quantities must be exactint0..1000000')
        delta=baseline-current;parsed.append((label,delta,Fraction(delta,baseline) if baseline else None))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'reductions':result,'total_delta':sum(row[1] for row in result),'increased':tuple(row[0] for row in result if row[1]<0),'scope':SCOPE}
