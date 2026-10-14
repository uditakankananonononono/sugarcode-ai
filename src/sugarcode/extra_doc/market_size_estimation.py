"""Row 360 Market Size Estimation: exact supplied-segment TAM/SAM/SOM funnel.

Calculates annual value from supplied segment customer counts, annual spend,
serviceable fractions and obtainable fractions. Returns exact segment and total
TAM, SAM and SOM, with SOM<=SAM<=TAM. No market data is inferred or invented.
Caps 64 segments, 32-bit rational inputs; counts are nonnegative integers.
NOT_CLAIMED: market research, factual forecast validation, competitive dynamics,
actual customer acquisition, investment advice or external reporting.
"""
from fractions import Fraction


def _number(v):
    if type(v) not in (int,Fraction):raise TypeError('values must be nonbool int or Fraction')
    if type(v) is int:
        if v.bit_length()>32:raise ValueError('values must fit 32 bits')
    elif v.numerator.bit_length()>32 or v.denominator.bit_length()>32:
        raise ValueError('values must fit 32 bits')
    return Fraction(v)


def market_funnel(segments):
    if type(segments) not in (list,tuple):raise TypeError('segments must be a list or tuple')
    if not 1<=len(segments)<=64:raise ValueError('segment count must be between 1 and 64')
    if any(type(s) not in (list,tuple) or len(s)!=4 for s in segments):
        raise ValueError('segments must contain count annual_spend serviceable obtainable')
    for count,spend,serviceable,obtainable in segments:
        if type(count) is not int or not 0<=count<=2**32-1:
            raise ValueError('customer counts must be nonbool integers zero through 4294967295')
    rows=[]
    for count,spend,serviceable,obtainable in segments:
        price=_number(spend);s=_number(serviceable);o=_number(obtainable)
        if price<0:raise ValueError('annual spend must be nonnegative')
        if not 0<=s<=1 or not 0<=o<=1:raise ValueError('fractions must be between zero and one')
        tam=count*price;sam=tam*s;som=sam*o
        rows.append({'tam':tam,'sam':sam,'som':som})
    totals={key:sum((row[key] for row in rows),Fraction(0)) for key in ('tam','sam','som')}
    return {'segments':rows,'totals':totals,'forecast_validated':False}
