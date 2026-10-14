import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc.race1756 import compare_rates
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_fraction_pairwise_gap_oracle():
    rng=random.Random(1756)
    for _ in range(100):
        groups=[]
        for i in range(10):
            t=rng.randint(1,1000);groups.append((str(i),rng.randint(0,t),t))
        fracs=[Fraction(p,t) for n,p,t in groups];gap=max(a-b for a in fracs for b in fracs)
        assert compare_rates(groups)=={'rates':[(n,(Fraction(p,t).numerator,Fraction(p,t).denominator)) for n,p,t in groups],'gap':(gap.numerator,gap.denominator),'claim':'PARTIAL','fairness_validated':False,'race_inferred':False}

@pytest.mark.parametrize('groups,message',[
 *[(x,'groups must be an exact list with 2..20 entries') for x in (None,L([('a',0,1),('b',0,1)]),(('a',0,1),('b',0,1)),[],[('a',0,1)],[(str(i),0,1) for i in range(21)])],
 *[([x,('b',0,1)],'group must be an id positive total tuple') for x in (['a',0,1],T(('a',0,1)),('a',0),('a',0,1,1))],
 *[([(x,0,1),('b',0,1)],'group IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',0,1),('a',1,1)],'group IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x,1000),('b',0,1)],'positive must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
 *[([('a',0,x),('b',0,1)],'total must be an integer in 1..1000') for x in (None,True,I(1),1.5,0,1001)],
 ([('a',2,1),('b',0,1)],'positive must not exceed total'),
])
def test_invalid(groups,message):
    with pytest.raises(ValueError) as exc:compare_rates(groups)
    assert str(exc.value)==message


def test_caps_zero_positive_fraction_and_gap():
    got=compare_rates([(str(i),1000,1000) for i in range(20)])
    assert got['rates']==[(str(i),(1,1)) for i in range(20)] and got['gap']==(0,1)
    assert compare_rates([('x'*80,0,1),('\u200b',1,1000)])['gap']==(1,1000)
