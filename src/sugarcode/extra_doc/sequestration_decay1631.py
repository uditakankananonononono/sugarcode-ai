"""Carbon Sequestration.

PARTIAL: caller stock-retention recurrence only, not carbon sequestration,
permanence certification,decay measurement or lifecycle emissions accounting.
Retention/additions supplied by caller,not validated storage process data.
"""
from fractions import Fraction
SCOPE='caller stock-retention recurrence only; no sequestration permanence or emissions claims'


def retain(additions,initial,num,den):
    """Additions exactlist/tuple1..64 exactint0..1000000;initial same int range.
    Retention components exactints0<=num<=den<=1000,den>0. Each step apply
    retention to previous stock then add current addition. Return exact stock
    after each step,loss each step,final stock,total losses. No physical units,
    rate calibration,permanence or external removal inferred. Order preserved.
    """
    if type(initial) is not int or not 0<=initial<=1000000:raise ValueError('initial must be exactint0..1000000')
    if type(num) is not int or type(den) is not int or not 0<=num<=den<=1000 or den==0:raise ValueError('retention components must be exactint0<=num<=den<=1000 and den>0')
    if type(additions) not in (list,tuple) or not 1<=len(additions)<=64:raise ValueError('additions must be exactlist/tuple length1..64')
    for addition in additions:
        if type(addition) is not int or not 0<=addition<=1000000:raise ValueError('addition must be exactint0..1000000')
    factor=Fraction(num,den);stock=Fraction(initial);stocks=[];losses=[]
    for addition in additions:
        loss=stock*(1-factor);stock=stock*factor+addition;losses.append(loss);stocks.append(stock)
    return {'stocks':tuple(stocks),'losses':tuple(losses),'final_stock':stock,'total_losses':sum(losses),'scope':SCOPE}
