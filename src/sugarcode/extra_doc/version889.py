"""Row889 Learning by Trial and Error: PARTIAL finite binary-conjunction version space.
Exact integer width1..4; observations exact list1..12 exact tuples(bits,outcome).
Bits exact tuple of width exact integers0..1,outcome exact integer0..1.
Hypotheses are tuples over(-1,0,1),where-1means wildcard. Enumerate every
hypothesis consistent with supplied labels; for every binary input report1if
all survivors predict1,0if all predict0,Noneif disagreement. Empty version
space returns None predictions and inconsistentTrue. No active experiment
selection, exploration policy, generalization or real-world truth claimed.
NOT_CLAIMED: valid labels, experiment selection, generalization, production readiness.
"""
from itertools import product
SCOPE='PARTIAL: exact finite binary-conjunction hypothesis elimination'
NOT_CLAIMED=('valid labels','experiment selection','generalization','production readiness')

def eliminate(width,observations):
    if type(width) is not int or not 1<=width<=4:raise ValueError('width must be exact int1..4')
    if type(observations) is not list or not 1<=len(observations)<=12:raise ValueError('observations must be exact list1..12')
    for row in observations:
        if type(row) is not tuple or len(row)!=2:raise ValueError('observation must be exact tuple2')
        bits,y=row
        if type(bits) is not tuple or len(bits)!=width:raise ValueError('bits must be exact aligned tuple')
        if any(type(v) is not int or not 0<=v<=1 for v in bits):raise ValueError('bits must be exact binary integers')
        if type(y) is not int or not 0<=y<=1:raise ValueError('outcome must be exact binary integer')
    def predict(h,b):return int(all(v==-1 or v==x for v,x in zip(h,b)))
    survivors=[h for h in product((-1,0,1),repeat=width) if all(predict(h,b)==y for b,y in observations)]
    predictions=[]
    for bits in product((0,1),repeat=width):
        values={predict(h,bits) for h in survivors};predictions.append((bits,next(iter(values)) if len(values)==1 else None))
    return {'hypotheses':survivors,'predictions':predictions,'inconsistent':not bool(survivors),'generalization_validated':False}
