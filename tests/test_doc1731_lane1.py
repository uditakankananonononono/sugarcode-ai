from collections import Counter
import random
import pytest
from sugarcode.extra_doc.focus_group1731 import audit


def test_independent_group_category_oracle():
    rng=random.Random(1731)
    for _ in range(100):
        rows=[(str(i),rng.choice('abc'),rng.choice('xyz')) for i in range(20)];sizes=Counter(g for n,g,c in rows);got=audit(rows,4,8)
        assert got['sizes']==sorted(sizes.items()) and got['size_flags']==[g for g,s in sorted(sizes.items()) if not 4<=s<=8]
        expected=[]
        for c in sorted({c for n,g,c in rows}):
            groups=sorted({g for n,g,cat in rows if cat==c})
            if len(groups)==1:expected.append((c,groups[0]))
        assert got['single_group_categories']==expected and got['claim']=='PARTIAL' and got['representation_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
@pytest.mark.parametrize('rows,lo,hi,message',[
 *[([],x,20,'bounds must be integers with 1<=minimum<=maximum<=20') for x in (True,I(1),0,21,1.5)],
 *[([],1,x,'bounds must be integers with 1<=minimum<=maximum<=20') for x in (True,I(1),0,21,1.5)],
 (L(),1,20,'participants must be an exact list with 0..100 entries'),
 ([(str(i),'a','b') for i in range(101)],1,20,'participants must be an exact list with 0..100 entries'),
 ([T(('a','b','c'))],1,20,'participants must be valid id group category tuples'),
 ([('a','b','c','d')],1,20,'participants must be valid id group category tuples'),
 *[([tuple(x if i==pos else 'a' for i in range(3))],1,20,'participants must be valid id group category tuples') for pos in range(3) for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a','b','c')]*2,1,20,'participant IDs must be unique'),
])
def test_invalid(rows,lo,hi,message):
    with pytest.raises(ValueError) as exc:audit(rows,lo,hi)
    assert str(exc.value)==message


def test_caps_and_exact_bounds():
    assert audit([(str(i),'a','b') for i in range(100)],1,20)['size_flags']==['a']
    assert audit([('x'*80,'\u200b','b')],1,1)['size_flags']==[]
    assert audit([],1,20)['sizes']==[]
