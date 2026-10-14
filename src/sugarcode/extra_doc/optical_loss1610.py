"""Optical Communications.

PARTIAL: caller multiplicative transmission-factor arithmetic only, not optical
communications, attenuation measurement, fiber modeling or achievable rates.
Factors are caller declarations, no wavelengths/materials or physics inferred.
"""
from fractions import Fraction
SCOPE='caller transmission-factor product only; no optical performance or rate claims'


def transmission(rows):
    """Rows exactlist/tuple0..64(label,numerator,denominator),unique printable
    Unicode exactstr label1..40;numerator exactint0..1000000,denominator exactint
    1..1000000,numerator<=denominator. Caller stage order preserved,return
    (label,exact cumulative transmission),final product and1-product loss.
    Empty product1. No dB conversion,noise,dispersion,power or hardware effects.
    Mixedrows accepted;factors not independently validated as optical models.
    """
    if type(rows) not in (list,tuple) or len(rows)>64:raise ValueError('rows must be exactlist/tuple atmost64')
    labels=set();stages=[];total=Fraction(1)
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(num) is not int or type(den) is not int or not 0<=num<=den<=1000000 or den==0:raise ValueError('factor components must be exactint0<=num<=den<=1000000 and den>0')
        total*=Fraction(num,den);stages.append((label,total))
    return {'stages':tuple(stages),'transmission':total,'loss':1-total,'scope':SCOPE}
