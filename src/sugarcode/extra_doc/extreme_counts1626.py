"""Extreme Weather.

PARTIAL: caller integer observation threshold count arithmetic only, not extreme
weather detection,return periods,climate attribution,forecasting or warnings.
Threshold/observations supplied by caller,no hazard classifications inferred.
"""
from fractions import Fraction
SCOPE='caller integer threshold counts only; no weather forecasts or hazard warnings'


def exceedance(values,threshold):
    """Values exactlist/tuple1..90 exactint-1000000..1000000;threshold same range.
    Strict exceedance value>threshold,equality not included. Return indices,
    count,exact fraction,and sum excess/max excess (0 if none). Preserve input
    order. No time inference,missing data,probability models or climate claims.
    """
    if type(threshold) is not int or not -1000000<=threshold<=1000000:raise ValueError('threshold must be exactint-1000000..1000000')
    if type(values) not in (list,tuple) or not 1<=len(values)<=90:raise ValueError('values must be exactlist/tuple length1..90')
    for value in values:
        if type(value) is not int or not -1000000<=value<=1000000:raise ValueError('value must be exactint-1000000..1000000')
    indices=tuple(i for i,value in enumerate(values) if value>threshold);excess=tuple(values[i]-threshold for i in indices)
    return {'indices':indices,'count':len(indices),'fraction':Fraction(len(indices),len(values)),
            'excess_sum':sum(excess),'max_excess':max(excess,default=0),'scope':SCOPE}
