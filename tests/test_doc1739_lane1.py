import random
import pytest
from sugarcode.extra_doc.panel1739 import audit


def test_independent_membership_join_oracle():
    rng=random.Random(1739)
    for _ in range(100):
        waves=[(str(i),rng.sample(list('abcdef'),rng.randrange(7))) for i in range(8)];expected=[]
        for (a,l),(b,r) in zip(waves,waves[1:]):expected.append((a,b,sorted(x for x in l if x in r),sorted(x for x in l if x not in r),sorted(x for x in r if x not in l)))
        got=audit(waves);assert got['changes']==expected and got['stable']==[x for x in 'abcdef' if all(x in m for n,m in waves)]
        assert got['claim']=='PARTIAL' and got['panel_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
@pytest.mark.parametrize('waves,message',[
 (L([('a',[]),('b',[])]),'waves must be an exact list with 2..20 entries'),
 ([('a',[])],'waves must be an exact list with 2..20 entries'),
 ([(str(i),[]) for i in range(21)],'waves must be an exact list with 2..20 entries'),
 ([T(('a',[])),('b',[])],'wave must be an id members tuple'),
 ([('a',[],1),('b',[])],'wave must be an id members tuple'),
 *[([(x,[]),('b',[])],'wave IDs must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[([('a',x),('b',[])],'members must be an exact list of 0..100 unique valid labels') for x in (L(),list(map(str,range(101))),[S('a')],['a','a'])],
])
def test_invalid(waves,message):
    with pytest.raises(ValueError) as exc:audit(waves)
    assert str(exc.value)==message


def test_caps_labels_empty_and_single_losses():
    members=list(map(str,range(100)));assert audit([(str(i),members[:]) for i in range(20)])['stable']==sorted(members)
    assert audit([('x'*80,['\u200b']),('b',[])])['changes'][0][3]==['\u200b']
    assert audit([('a',[]),('b',[])])['stable']==[]

@pytest.mark.parametrize('waves,message',[
 ((('a',[]),('b',[])),'waves must be an exact list with 2..20 entries'),
 ([['a',[]],('b',[])],'wave must be an id members tuple'),
 ([('a',),('b',[])],'wave must be an id members tuple'),
 ([('a',[]),('a',[])],'wave IDs must be unique valid labels'),
 *[([('a',[x]),('b',[])],'members must be an exact list of 0..100 unique valid labels') for x in (None,False,1,'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ([('a',('x',)),('b',[])],'members must be an exact list of 0..100 unique valid labels'),
])
def test_extra_shapes(waves,message):
    with pytest.raises(ValueError) as exc:audit(waves)
    assert str(exc.value)==message


def test_member_label_cap():
    assert audit([('a',['x'*80]),('b',['x'*80])])['stable']==['x'*80]
