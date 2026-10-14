import random
import pytest
from sugarcode.extra_doc.survey1722 import audit


def test_independent_query_oracle():
    rng=random.Random(1722)
    for _ in range(100):
        constructs=['a','b','c'];rows=[(str(i),rng.choice('abcd'),bool(rng.randrange(2))) for i in range(10)]
        got=audit(constructs,rows)
        assert got['uncovered']==[c for c in constructs if not any(q[1]==c for q in rows)]
        assert got['optional_only']==[c for c in constructs if any(q[1]==c for q in rows) and not any(q[1]==c and q[2] for q in rows)]
        assert got['unknown']==[q[0] for q in rows if q[1] not in constructs]
        assert got['claim']=='PARTIAL' and got['survey_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
@pytest.mark.parametrize('constructs,rows,message',[
 (L(['a']),[],'constructs must be an exact list with 1..20 entries'),
 ([],[],'constructs must be an exact list with 1..20 entries'),
 ([str(i) for i in range(21)],[],'constructs must be an exact list with 1..20 entries'),
 *[([x],[],'constructs must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 (['a','a'],[],'constructs must be unique valid labels'),
 (['a'],L(),'questions must be an exact list with 0..50 entries'),
 (['a'],[(str(i),'a',True) for i in range(51)],'questions must be an exact list with 0..50 entries'),
 (['a'],[T(('a','a',True))],'question must be an id construct required tuple'),
 (['a'],[('a','a',True,True)],'question must be an id construct required tuple'),
 (['a'],[(S('a'),'a',True)],'question IDs must be unique valid labels'),
 (['a'],[('a',S('a'),True)],'question construct must be a valid label'),
 *[(['a'],[('a','a',x)],'required must be an exact boolean') for x in (0,1,1.5,None)],
])
def test_invalid(constructs,rows,message):
    with pytest.raises(ValueError) as exc:audit(constructs,rows)
    assert str(exc.value)==message


def test_caps_labels():
    constructs=[str(i) for i in range(20)];rows=[(str(i),str(i%20),True) for i in range(50)]
    assert audit(constructs,rows)['uncovered']==[]
    assert audit(['x'*80],[('\u200b','x'*80,False)])['optional_only']==['x'*80]
