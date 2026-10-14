import random
import pytest
from sugarcode.extra_doc.organization1760 import audit_structure
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_root_expansion_oracle():
    rng=random.Random(1760)
    for _ in range(100):
        rows=[('0',None)]+[(str(i),str(rng.randrange(i))) for i in range(1,30)];rng.shuffle(rows)
        depths={'0':0}
        while len(depths)<30:
            for n,p in rows:
                if n not in depths and p in depths:depths[n]=depths[p]+1
        reports=[(n,sorted(a for a,p in rows if p==n)) for n,pp in rows]
        assert audit_structure(rows)=={'root':'0','depths':[(n,depths[n]) for n,p in rows],'direct_reports':reports,'claim':'PARTIAL','organization_validated':False}

@pytest.mark.parametrize('members,message',[
 *[(x,'members must be an exact list with 1..100 entries') for x in (None,L([('a',None)]),(('a',None),),[],[(str(i),None) for i in range(101)])],
 *[([x],'member must be an id manager tuple') for x in (['a',None],T(('a',None)),('a',),('a',None,1))],
 *[([(x,None)],'member IDs must be unique valid labels') for x in BAD],
 ([('a',None),('a',None)],'member IDs must be unique valid labels'),
 *[([('a',x)],'manager must be None or a valid label') for x in BAD if x is not None],
 ([('a','unknown')],'managers must be known distinct members'),
 ([('a','a')],'managers must be known distinct members'),
 ([('a',None),('b',None)],'exactly one root is required'),
 ([('a','b'),('b','a')],'exactly one root is required'),
 ([('a',None),('b','c'),('c','b')],'reporting cycles are forbidden'),
])
def test_invalid(members,message):
    with pytest.raises(ValueError) as exc:audit_structure(members)
    assert str(exc.value)==message


def test_cap_deep_chain_and_zero_width_root():
    rows=[('x'*80,None),('\u200b','x'*80)]+[(str(i),'\u200b' if i==0 else str(i-1)) for i in range(98)]
    assert audit_structure(rows)['depths'][-1]==('97',99)
    assert audit_structure([('a',None)])['direct_reports']==[('a',[])]
