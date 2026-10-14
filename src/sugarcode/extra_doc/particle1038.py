"""Doc row1038 Particle Filters: PARTIAL deterministic systematic resampling.

weights exact list1..50 nonbool ints0..100, positive sum; count exact int1..50;
offset exact tuple(num,den), ints0<=num<den<=100. Draw points (j+offset)/count,
select first cumulative normalized weight STRICTLY greater than point. Return
input particle indexes; zero weights never selected. No filtering model, random
offset, unbiasedness verification or inference accuracy claim.
"""
from fractions import Fraction


def resample(weights,count,offset):
    if type(weights) is not list or not 1<=len(weights)<=50:
        raise ValueError('weights must be an exact list with 1..50 entries')
    if any(type(x) is not int or not 0<=x<=100 for x in weights) or sum(weights)==0:
        raise ValueError('weights must be integers in 0..100 with positive sum')
    if type(count) is not int or not 1<=count<=50:
        raise ValueError('count must be an integer in 1..50')
    if type(offset) is not tuple or len(offset)!=2 or any(type(x) is not int for x in offset) or not 0<=offset[0]<offset[1]<=100:
        raise ValueError('offset must be an exact integer fraction with 0<=num<den<=100')
    total=sum(weights);cumulative=[];running=0
    for weight in weights:running+=weight;cumulative.append(Fraction(running,total))
    selected=[];u=Fraction(*offset)
    for j in range(count):
        point=(j+u)/count
        selected.append(next(i for i,c in enumerate(cumulative) if c>point))
    return {'indexes':selected,'claim':'PARTIAL','filter_validated':False}
