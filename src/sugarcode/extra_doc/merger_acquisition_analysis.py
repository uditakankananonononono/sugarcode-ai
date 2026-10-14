"""Row508 M&A Analysis: exact finite supplied synergy discounted-value analysis.

Standalone target value plus present value of supplied end-period synergies
minus purchase price/integration cost gives acquisition NPV. Break-even price
is standalone+synergyPV-integration. Caps24periods/32bitmagnitude cashflows,
nonnegative32bitprices/values/cost;discount basispoints0..10000.
NOT_CLAIMED: real acquisition evaluation, forecast truth, diligence, taxes,
financing, legal advice, investment recommendation or transaction execution.
"""
from fractions import Fraction


def acquisition_value(standalone_value,purchase_price,integration_cost,synergies,discount_bps):
    if type(synergies) not in (list,tuple):raise TypeError('synergies must be a list or tuple')
    if not 1<=len(synergies)<=24:raise ValueError('synergy period count must be between 1 and 24')
    if any(type(v) is not int or not 0<=v<=2**32-1 for v in (standalone_value,purchase_price,integration_cost)):
        raise ValueError('values prices and costs must be nonbool integers zero through 4294967295')
    if any(type(v) is not int or v.bit_length()>32 for v in synergies):raise ValueError('synergies must be nonbool 32-bit magnitude signed integers')
    if type(discount_bps) is not int or not 0<=discount_bps<=10000:raise ValueError('discount must be nonbool integer zero through 10000 basis points')
    factor=1+Fraction(discount_bps,10000);flows=[Fraction(v)/factor**(i+1) for i,v in enumerate(synergies)]
    pv=sum(flows,Fraction(0));price=standalone_value+pv-integration_cost;npv=price-purchase_price
    return {'discounted_synergies':flows,'synergy_present_value':pv,'break_even_price':price,
            'acquisition_npv':npv,'positive_npv':npv>0,'transaction_performed':False}
