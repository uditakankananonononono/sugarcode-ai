"""Row1174 Health Screening Recommendations: PARTIAL supplied decision curve.
Exact list1..24 tuples(label,pnum,pden,outcome): unique printable ASCII
labels1..24, exact integers pnum0..10,pden1..10,pnum<=pden,outcome0..1.
Thresholds exact tuple1..8 of unique exact integer percentages1..99.
At each supplied threshold t, select probability>=t. Return TP,FP and net
benefit TP/N-FP/N*t/(1-t), treat-all prevalence-(1-prevalence)*t/(1-t),
and treat-none zero. Scores/outcomes/time horizon/cost tradeoff supplied, not
validated; no screening recommendation, threshold selection or clinical advice.
NOT_CLAIMED: calibration, clinical utility, screening advice, production readiness.
"""
from fractions import Fraction as F
SCOPE='PARTIAL: exact supplied threshold decision-curve arithmetic only'
NOT_CLAIMED=('calibration','clinical utility','screening advice','production readiness')

def curve(rows,thresholds):
    if type(rows) is not list or not 1<=len(rows)<=24:raise ValueError('rows must be exact list1..24')
    if type(thresholds) is not tuple or not 1<=len(thresholds)<=8:raise ValueError('thresholds must be exact tuple1..8')
    seen=set()
    for t in thresholds:
        if type(t) is not int or not 1<=t<=99 or t in seen:raise ValueError('unique exact thresholds1..99 required')
        seen.add(t)
    seen=set()
    for row in rows:
        if type(row) is not tuple or len(row)!=4:raise ValueError('row must be exact tuple4')
        label,a,b,y=row
        if type(label) is not str or not 1<=len(label)<=24 or not (label.isascii() and label.isprintable()) or label in seen:raise ValueError('labels must be unique printable ASCII strings1..24')
        seen.add(label)
        if type(a) is not int or not 0<=a<=10 or type(b) is not int or not 1<=b<=10 or a>b:raise ValueError('exact bounded probability counts required')
        if type(y) is not int or not 0<=y<=1:raise ValueError('outcome must be exact int0..1')
    n=len(rows);prevalence=F(sum(r[3] for r in rows),n);trace=[]
    for t in thresholds:
        chosen=[r for r in rows if 100*r[1]>=t*r[2]];tp=sum(r[3] for r in chosen);fp=len(chosen)-tp;odds=F(t,100-t)
        trace.append((t,tp,fp,F(tp,n)-F(fp,n)*odds,prevalence-(1-prevalence)*odds,F(0)))
    return {'curve':trace,'clinical_validated':False}
