"""Hydrogen Economy.

PARTIAL: caller staged conversion-factor chain only, not hydrogen economy,
production/storage/transport physics,efficiency validation or cost analysis.
Input/factors caller abstractions,no actual hydrogen quantities inferred.
"""
from fractions import Fraction
SCOPE='caller staged conversion-factor chain only; no hydrogen performance or cost claims'


def chain(rows,initial):
    """Rows exactlist/tuple0..64(label,num,den),unique printable Unicode exactstr
    1..40 labels;exactints0<=num<=den<=1000000,den>0;initial exactint0..1000000.
    Preserve stage order. Return(label,remaining,stage loss),final quantity,total
    losses. Exact Fractions;empty chain final=initial. No energy/mass conversion,
    units,leakage chemistry,emissions or economic assumptions. Mixedrows accepted.
    """
    if type(initial) is not int or not 0<=initial<=1000000:raise ValueError('initial must be exactint0..1000000')
    if type(rows) not in (list,tuple) or len(rows)>64:raise ValueError('rows must be exactlist/tuple atmost64')
    labels=set();parsed=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(num) is not int or type(den) is not int or not 0<=num<=den<=1000000 or den==0:raise ValueError('factor components must be exactint0<=num<=den<=1000000 and den>0')
        parsed.append((label,Fraction(num,den)))
    quantity=Fraction(initial);result=[]
    for label,factor in parsed:
        after=quantity*factor;result.append((label,after,quantity-after));quantity=after
    return {'stages':tuple(result),'final':quantity,'total_losses':initial-quantity,'scope':SCOPE}
