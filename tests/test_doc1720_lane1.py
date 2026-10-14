from fractions import Fraction
import random
import pytest
from sugarcode.extra_doc.triple_bottom1720 import rank


def test_independent_normalized_weights_oracle():
    rng=random.Random(1720)
    for _ in range(100):
        rows=[(str(i),*[rng.randrange(101) for _ in range(3)]) for i in range(15)];weights=tuple(rng.randrange(1,11) for _ in range(3))
        ws=[Fraction(w,sum(weights)) for w in weights];scores=[(r[0],sum(ws[j]*r[j+1] for j in range(3))) for r in rows]
        got=rank(rows,weights)
        assert got['ranking']==[(n,(s.numerator,s.denominator)) for n,s in sorted(scores,key=lambda r:(-r[1],r[0]))]
        assert got['claim']=='PARTIAL' and got['value_judgments_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('rows,weights,message',[
 (L([('a',0,0,0)]),(1,1,1),'rows must be an exact list with 1..50 entries'),
 ([],(1,1,1),'rows must be an exact list with 1..50 entries'),
 ([(str(i),0,0,0) for i in range(51)],(1,1,1),'rows must be an exact list with 1..50 entries'),
 *[([('a',0,0,0)],x,'weights must be an exact triple of integers in 0..10 with positive sum') for x in (T((1,1,1)),(1,1),(1,1,1,1),(True,1,1),(1,I(1),1),(1,1,1.5),(-1,1,1),(11,1,1),(0,0,0))],
 ([T(('a',0,0,0))],(1,1,1),'row must be an id people planet profit tuple'),
 ([('a',0,0,0,0)],(1,1,1),'row must be an id people planet profit tuple'),
 *[([(x,0,0,0)],(1,1,1),'IDs must be unique nonblank exact strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([tuple('a' if j==0 else x if j==pos else 0 for j in range(4))],(1,1,1),'metrics must be exact integers in 0..100') for pos in (1,2,3) for x in (True,I(0),-1,101,1.5)],
])
def test_invalid(rows,weights,message):
    with pytest.raises(ValueError) as exc:rank(rows,weights)
    assert str(exc.value)==message


def test_maxima_zero_weight_ties_labels():
    assert len(rank([(str(i),100,100,100) for i in range(50)],(10,10,10))['ranking'])==50
    assert rank([('x'*80,100,0,0)],(10,0,0))['ranking'][0][1]==(100,1)
    assert rank([('b',0,0,0),('\u200b',0,0,0)],(1,1,1))['ranking'][0][0]=='b'
