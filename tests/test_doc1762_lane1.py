import random
from fractions import Fraction
import pytest
from sugarcode.extra_doc.political1762 import audit_sectors
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass


def test_independent_vector_ledger_oracle():
    rng=random.Random(1762)
    for _ in range(100):
        rows=[(str(i),rng.randrange(1001),rng.randrange(1001)) for i in range(10)];revenues=[r for n,r,c in rows];costs=[c for n,r,c in rows];total=sum(revenues)
        assert audit_sectors(rows)=={'balances':[(n,sum([r,-c])) for n,r,c in rows],'totals':(total,sum(costs),sum(r-c for n,r,c in rows)),'revenue_shares':[(n,(Fraction(r,total).numerator,Fraction(r,total).denominator)) for n,r,c in rows],'claim':'PARTIAL','economy_validated':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'sectors must be an exact list with 1..20 entries') for x in (None,L([('a',0,0)]),(('a',0,0),),[],[(str(i),0,0) for i in range(21)])],
 *[([x],'sector must be an id revenue cost tuple') for x in (['a',0,0],T(('a',0,0)),('a',0),('a',0,0,1))],
 *[([(x,0,0)],'sector IDs must be unique nonblank exact strings of 1..80 characters') for x in (None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',0,0),('a',1,1)],'sector IDs must be unique nonblank exact strings of 1..80 characters'),
 *[([('a',x,0)],'revenue must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
 *[([('a',0,x)],'cost must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_sectors(rows)
    assert str(exc.value)==message


def test_caps_singleton_zero_negative_balance():
    got=audit_sectors([(str(i),1000,1000) for i in range(20)]);assert got['totals']==(20000,20000,0) and got['revenue_shares']==[(str(i),(1,20)) for i in range(20)]
    assert audit_sectors([('x'*80,0,1000)])['revenue_shares']==[('x'*80,None)]
    assert audit_sectors([('\u200b',0,1000)])['balances']==[('\u200b',-1000)]
