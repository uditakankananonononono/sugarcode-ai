import random
import pytest
from sugarcode.extra_doc.participant1733 import audit


def test_independent_slot_join_oracle():
    rng=random.Random(1733)
    for _ in range(100):
        slots=[('a','x'),('b','y')];rows=[(str(i),rng.choice('ab'),rng.choice('xy'),rng.randrange(1,61)) for i in range(20)];got=audit(slots,rows)
        expected=[]
        for s,a in slots:
            matching=[d for n,setting,activity,d in rows if setting==s and activity==a];expected.append((s,a,len(matching),sum(matching)))
        assert got['coverage']==expected and got['uncovered']==[(s,a) for s,a,n,d in expected if not n]
        assert got['unknown']==[n for n,s,a,d in rows if (s,a) not in slots]
        assert got['claim']=='PARTIAL' and got['observation_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('slots,rows,message',[
 (L([('a','x')]),[],'slots must be an exact list with 1..50 entries'),
 ([],[],'slots must be an exact list with 1..50 entries'),
 ([(str(i),'x') for i in range(51)],[],'slots must be an exact list with 1..50 entries'),
 ([T(('a','x'))],[],'slots must be unique valid setting activity tuples'),
 *[([(x,'a')],[],'slots must be unique valid setting activity tuples') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a','x')],L(),'observations must be an exact list with 0..100 entries'),
 ([('a','x')],[(str(i),'a','x',1) for i in range(101)],'observations must be an exact list with 0..100 entries'),
 ([('a','x')],[T(('id','a','x',1))],'observation must be an id setting activity duration tuple'),
 ([('a','x')],[('id','a','x',1,1)],'observation must be an id setting activity duration tuple'),
 *[([('a','x')],[tuple(x if i==pos else ['id','a','x',1][i] for i in range(4))],'observation labels must be valid with unique IDs') for pos in range(3) for x in (S('a'),'\t')],
 *[([('a','x')],[('id','a','x',x)],'duration must be an integer in 1..60') for x in (True,I(1),0,61,1.5)],
])
def test_invalid(slots,rows,message):
    with pytest.raises(ValueError) as exc:audit(slots,rows)
    assert str(exc.value)==message


def test_caps_labels_and_empty_observations():
    slots=[(str(i),'x'*80) for i in range(50)];rows=[(str(i),str(i%50),'x'*80,60) for i in range(100)]
    assert all(n==2 and d==120 for s,a,n,d in audit(slots,rows)['coverage'])
    assert audit([('\u200b','x')],[])['uncovered']==[('\u200b','x')]
