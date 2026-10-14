import random
import pytest
from sugarcode.extra_doc.questionnaire1723 import audit


def test_independent_answer_join_oracle():
    rng=random.Random(1723)
    for _ in range(100):
        rows=[(str(i),['a','b'],bool(rng.randrange(2))) for i in range(8)]
        answers={str(i):rng.choice('abc') for i in range(10) if rng.randrange(2)};got=audit(rows,answers)
        assert got['missing']==[n for n,c,r in rows if r and not any(n==k for k in answers)]
        assert got['unknown']==[k for k in answers if not any(k==n for n,c,r in rows)]
        assert got['invalid_choices']==[n for n,c,r in rows if n in answers and all(answers[n]!=x for x in c)]
        assert got['claim']=='PARTIAL' and got['measurement_validated'] is False

class L(list):pass
class T(tuple):pass
class D(dict):pass
class S(str):pass
@pytest.mark.parametrize('rows,answers,message',[
 (L([('a',['x','y'],True)]),{},'questions must be an exact list with 1..50 entries'),
 ([],{},'questions must be an exact list with 1..50 entries'),
 ([(str(i),['x','y'],True) for i in range(51)],{},'questions must be an exact list with 1..50 entries'),
 ([T(('a',['x','y'],True))],{},'question must be an id choices required tuple'),
 ([('a',['x','y'],True,True)],{},'question must be an id choices required tuple'),
 *[([(x,['a','b'],True)],{},'question IDs must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('a',x,True)],{},'choices must be an exact list of 2..10 unique valid labels') for x in (L(['a','b']),['a'],list(map(str,range(11))),['a','a'],[S('a'),'b'])],
 ([('a',['x','y'],1)],{},'required must be an exact boolean'),
 ([('a',['x','y'],True)],D(),'answers must be an exact dict with 0..50 entries'),
 ([('a',['x','y'],True)],{str(i):'x' for i in range(51)},'answers must be an exact dict with 0..50 entries'),
 ([('a',['x','y'],True)],{S('a'):'x'},'answer IDs and values must be valid labels'),
 ([('a',['x','y'],True)],{'a':S('x')},'answer IDs and values must be valid labels'),
])
def test_invalid(rows,answers,message):
    with pytest.raises(ValueError) as exc:audit(rows,answers)
    assert str(exc.value)==message


def test_caps_labels_and_missing_optional():
    choices=list(map(str,range(10)));rows=[(str(i),choices[:],True) for i in range(50)];answers={str(i):'0' for i in range(50)}
    assert audit(rows,answers)['missing']==[]
    assert audit([('x'*80,['a','\u200b'],False)],{})['missing']==[]
