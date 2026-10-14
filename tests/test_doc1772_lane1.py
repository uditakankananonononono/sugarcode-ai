import random
import itertools
import pytest
from sugarcode.extra_doc.revolution1772 import audit_changes
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_time_bucket_run_oracle():
    rng=random.Random(1772)
    for _ in range(100):
        rows=[(t,rng.choice('abc')) for t in rng.sample(range(1001),30)];rng.shuffle(rows);buckets={t:s for t,s in rows};ordered=[(t,buckets[t]) for t in range(1001) if t in buckets];runs=[]
        for label,group in itertools.groupby(ordered,key=lambda x:x[1]):
            points=list(group);runs.append((label,points[0][0],points[-1][0],len(points)))
        changes=[(*ordered[i],*ordered[i+1]) for i in range(29) if ordered[i][1]!=ordered[i+1][1]]
        assert audit_changes(rows)=={'changes':changes,'runs':runs,'claim':'PARTIAL','revolution_inferred':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'observations must be an exact list with 2..100 entries') for x in (None,L([(0,'a'),(1,'b')]),((0,'a'),(1,'b')),[],[(0,'a')],[(i,'a') for i in range(101)])],
 *[([x,(1,'b')],'observation must be a time label tuple') for x in ([0,'a'],T((0,'a')),(0,),(0,'a',1))],
 *[([(x,'a'),(1,'b')],'times must be unique exact integers in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
 ([(0,'a'),(0,'b')],'times must be unique exact integers in 0..1000'),
 *[([(0,x),(1,'b')],'labels must be nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_changes(rows)
    assert str(exc.value)==message


def test_caps_minimum_and_repeated_separated_label():
    assert audit_changes([(i,'x'*80) for i in range(100)])['runs']==[('x'*80,0,99,100)]
    assert audit_changes([(1000,'\u200b'),(0,'a')])['changes']==[(0,'a',1000,'\u200b')]
    rows=[(0,'a'),(1,'b'),(2,'a')];out=audit_changes(rows);assert len(out['runs'])==3;out['runs'].clear();assert rows==[(0,'a'),(1,'b'),(2,'a')]
