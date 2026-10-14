"""Row 362 Porter's Five Forces: exact supplied-pressure attractiveness model.

Five inputs in order: rivalry, entrants, substitutes, suppliers, buyers.
Weighted pressure is sum(score*weight)/sum(weights); attractiveness is 100
minus pressure. Force contributions expose the supplied score model.
Scores 0..100, weights 0..1000; exact Fraction arithmetic.
NOT_CLAIMED: factual industry measurement, research, investment prediction,
validated attractiveness, qualitative strategic analysis or business success.
"""
from fractions import Fraction
FORCES=('rivalry','entrants','substitutes','suppliers','buyers')


def industry_attractiveness(pressures,weights):
    if type(pressures) not in (list,tuple) or type(weights) not in (list,tuple):
        raise TypeError('inputs must be lists or tuples')
    if len(pressures)!=5 or len(weights)!=5:raise ValueError('exactly five pressures and weights required')
    if any(type(v) is not int or not 0<=v<=100 for v in pressures):
        raise ValueError('pressures must be nonbool integers zero through 100')
    if any(type(v) is not int or not 0<=v<=1000 for v in weights):
        raise ValueError('weights must be nonbool integers zero through 1000')
    total=sum(weights)
    if total==0:raise ValueError('at least one weight must be positive')
    contributions=[Fraction(p*w,total) for p,w in zip(pressures,weights)]
    pressure=sum(contributions,Fraction(0));attractiveness=100-pressure
    return {'forces':[{'force':name,'pressure':p,'contribution':c} for name,p,c in zip(FORCES,pressures,contributions)],
            'weighted_pressure':pressure,'attractiveness':attractiveness,'assessment_validated':False}
