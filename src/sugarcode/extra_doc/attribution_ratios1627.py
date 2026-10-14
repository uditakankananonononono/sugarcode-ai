"""Climate Attribution.

PARTIAL: caller event-frequency ratio arithmetic only, not climate attribution,
causal inference,observational estimates or scientific confidence statements.
Two count pairs are caller declarations,not validated factual/counterfactual data.
"""
from fractions import Fraction
SCOPE='caller event-frequency ratios only; no causal climate attribution claims'


def ratio(left,right):
    """Each exactlist/tuple(count,total),exactint1<=count<=total<=1000000.
    Return exact left/right frequencies,frequency ratio,and1-right/left fraction.
    Counts strictly positive to avoid undefined ratios. No causal labels,
    significance,uncertainty,model ensembles or physical attribution inferred.
    """
    def frequency(row):
        if type(row) not in (list,tuple) or len(row)!=2:raise ValueError('count pair must be exactlist/tuple pair')
        count,total=row
        if type(count) is not int or type(total) is not int or not 1<=count<=total<=1000000:raise ValueError('counts must be exactint1<=count<=total<=1000000')
        return Fraction(count,total)
    a=frequency(left);b=frequency(right)
    return {'left_frequency':a,'right_frequency':b,'ratio':a/b,'relative_fraction':1-b/a,'scope':SCOPE}
