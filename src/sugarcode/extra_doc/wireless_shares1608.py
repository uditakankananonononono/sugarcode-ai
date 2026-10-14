"""Wireless Communications.

PARTIAL: caller weighted resource-share arithmetic only, not wireless
communications, airtime scheduling, interference modeling or achievable rates.
Weights/capacity are caller abstractions; no actual radio resources allocated.
"""
from fractions import Fraction
SCOPE='caller weighted resource shares only; no wireless scheduling or rate claims'


def shares(rows,capacity):
    """Rows exactlist/tuple1..64(label,weight),unique printable Unicode exactstr
    label1..40,weight exactint1..1000000;capacity exactint0..1000000. Return
    label-sorted(label,weight/sumweights,capacity*weight/sumweights) exact
    Fractions and total capacity. No integer rounding,minimum guarantees,
    device discovery or RF effects. Mixedrowcontainers accepted both orders.
    """
    if type(capacity) is not int or not 0<=capacity<=1000000:raise ValueError('capacity must be exactint0..1000000')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('row must be exactlist/tuple pair')
        label,weight=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(weight) is not int or not 1<=weight<=1000000:raise ValueError('weight must be exactint1..1000000')
        parsed.append((label,weight))
    total=sum(weight for _,weight in parsed)
    result=tuple((label,Fraction(weight,total),Fraction(capacity*weight,total)) for label,weight in sorted(parsed,key=lambda row:row[0]))
    return {'shares':result,'capacity':capacity,'scope':SCOPE}
