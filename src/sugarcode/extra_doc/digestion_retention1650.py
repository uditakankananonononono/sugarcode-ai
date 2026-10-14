"""Anaerobic Digestion.

PARTIAL: caller volume/flow retention arithmetic only, not anaerobic digestion,
microbial kinetics, gas yield, equipment sizing or operational safety advice.
Caller values are abstract compatible units, not verified process measurements.
"""
from fractions import Fraction
SCOPE='caller volume-flow retention arithmetic only; no anaerobic digestion advice'


def retention(rows,threshold):
    """Exactlist/tuple1..64 triples(label,volume,flow);unique printable Unicode
    exactstr labels1..40;exactint volume0..1000000,flow1..1000000;threshold
    exactint0..1000000 caller comparison only. Sorted(label,volume/flow),
    strictly below-threshold labels and maximum retention. No biological
    sufficiency or process effectiveness inferred. Mixedrows accepted.
    """
    if type(threshold) is not int or not 0<=threshold<=1000000:raise ValueError('threshold must be exactint0..1000000')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,volume,flow=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(volume) is not int or type(flow) is not int or not 0<=volume<=1000000 or not 1<=flow<=1000000:raise ValueError('volume must be exactint0..1000000 and flow exactint1..1000000')
        parsed.append((label,Fraction(volume,flow)))
    result=tuple(sorted(parsed,key=lambda row:row[0]))
    return {'retention':result,'below':tuple(label for label,value in result if value<threshold),'maximum':max(value for label,value in result),'scope':SCOPE}
