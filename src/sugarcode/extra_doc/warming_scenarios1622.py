"""Global Warming Projections.

PARTIAL: caller linear scenario arithmetic only, not warming projections,
climate forecasts,emissions-response estimates or scientific confidence bounds.
Slopes/intercepts supplied by caller without physical calibration or validation.
"""
from fractions import Fraction
SCOPE='caller linear scenario arithmetic only; no global-warming projections'


def scenarios(rows,steps):
    """Rows exactlist/tuple1..32(label,intercept,slope_num,slope_den),unique
    printable Unicode exactstr label1..40;intercept/slope_num exactint-1000000..
    1000000,slope_den exactint1..1000000;steps exactlist/tuple1..32 unique exact
    int0..100000. Return label-sorted series(step,intercept+step*slope),step-sorted
    values;envelope(step,min,max) across declared scenarios. Envelope is not a
    confidence interval. Mixedrows accepted;no physical units or dates inferred.
    """
    if type(steps) not in (list,tuple) or not 1<=len(steps)<=32:raise ValueError('steps must be exactlist/tuple length1..32')
    for step in steps:
        if type(step) is not int or not 0<=step<=100000:raise ValueError('step must be exactint0..100000')
    if len(set(steps))!=len(steps):raise ValueError('steps must be unique')
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=32:raise ValueError('rows must be exactlist/tuple length1..32')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=4:raise ValueError('row must be exactlist/tuple four values')
        label,intercept,num,den=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(intercept) is not int or type(num) is not int or not -1000000<=intercept<=1000000 or not -1000000<=num<=1000000:raise ValueError('intercept and numerator must be exactint-1000000..1000000')
        if type(den) is not int or not 1<=den<=1000000:raise ValueError('denominator must be exactint1..1000000')
        result.append((label,tuple((step,Fraction(intercept)+step*Fraction(num,den)) for step in sorted(steps))))
    result.sort(key=lambda row:row[0]);envelope=tuple((step,min(series[i][1] for _,series in result),max(series[i][1] for _,series in result)) for i,step in enumerate(sorted(steps)))
    return {'scenarios':tuple(result),'envelope':envelope,'scope':SCOPE}
