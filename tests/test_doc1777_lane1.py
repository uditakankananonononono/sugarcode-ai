import random
import copy
import pytest
from sugarcode.extra_doc.race_relations1777 import count_contacts
class L(list):pass
class T(tuple):pass
class S(str):pass
class I(int):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_contact_matrix_oracle():
    rng=random.Random(1777);categories=list('abcd')
    for _ in range(100):
        rng.shuffle(categories);rows=[(rng.choice(categories),rng.choice(categories),rng.randrange(1001)) for i in range(50)]
        matrix=[[sum(n for aa,bb,n in rows if aa==a and bb==b) for b in categories] for a in categories]
        pairs=[(a,b,matrix[i][j]) for i,a in enumerate(categories) for j,b in enumerate(categories) if matrix[i][j]]
        same=sum(matrix[i][i] for i in range(4));different=sum(sum(row) for row in matrix)-same
        assert count_contacts(categories,rows)=={'pairs':pairs,'same':same,'different':different,'claim':'PARTIAL','race_inferred':False}

@pytest.mark.parametrize('categories',[None,L(['a','b']),('a','b'),[],['a'],list(map(str,range(21))),['a','a'],*[[x,'b'] for x in BAD]])
def test_categories_invalid(categories):
    with pytest.raises(ValueError) as exc:count_contacts(categories,[])
    assert str(exc.value)=='categories must be an exact list of 2..20 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'contacts must be an exact list with 0..100 entries') for x in (None,L(),(),[('a','b',1)]*101)],
 *[([x],'contact must be a source target count tuple') for x in (['a','b',1],T(('a','b',1)),('a','b'),('a','b',1,1))],
 *[([(x,'b',1)],'endpoints must be known valid labels') for x in (*BAD,'unknown')],
 *[([('a',x,1)],'endpoints must be known valid labels') for x in (*BAD,'unknown')],
 *[([('a','b',x)],'count must be an integer in 0..1000') for x in (None,True,I(0),1.5,-1,1001)],
])
def test_contacts_invalid(rows,message):
    with pytest.raises(ValueError) as exc:count_contacts(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_duplicates_empty_zero_count_and_ownership():
    cats=['x'*80,'\u200b']+list(map(str,range(18)));rows=[('x'*80,'\u200b',1000)]*100;before=copy.deepcopy(rows);out=count_contacts(cats,rows)
    assert out['different']==100000 and out['pairs']==[('x'*80,'\u200b',100000)]
    out['pairs'].clear();assert rows==before
    assert count_contacts(['a','b'],[])['pairs']==[]
    assert count_contacts(['a','b'],[('a','a',0)])['same']==0
