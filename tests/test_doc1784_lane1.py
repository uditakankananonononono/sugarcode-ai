import random
import copy
import pytest
from sugarcode.extra_doc.exclusion1784 import audit_access
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_access_matrix_oracle():
    rng=random.Random(1784);services=list('abcd')
    for _ in range(100):
        rng.shuffle(services);rows=[(str(i),rng.sample(services,rng.randrange(5))) for i in range(20)];matrix=[[int(s in a) for s in services] for n,a in rows]
        assert audit_access(services,rows)=={'missing':[(n,[s for j,s in enumerate(services) if not matrix[i][j]]) for i,(n,a) in enumerate(rows)],'no_access':[n for (n,a),r in zip(rows,matrix) if sum(r)==0],'full_access':[n for (n,a),r in zip(rows,matrix) if sum(r)==4],'claim':'PARTIAL','exclusion_inferred':False}

@pytest.mark.parametrize('services',[None,L(['a']),('a',),[],list(map(str,range(21))),['a','a'],*[[x] for x in BAD]])
def test_services_invalid(services):
    with pytest.raises(ValueError) as exc:audit_access(services,[('r',[])])
    assert str(exc.value)=='services must be an exact list of 1..20 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'records must be an exact list with 1..100 entries') for x in (None,L([('a',[])]),(('a',[]),),[],[(str(i),[]) for i in range(101)])],
 *[([x],'record must be an id accessible tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[])],'record IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'record IDs must be unique valid labels'),
 *[([('a',x)],'accessible must be an exact list of 0..20 unique known service labels') for x in (None,L(),('a',),['a','a'],['unknown'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_records_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_access(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_singletons_empty_and_ownership():
    services=['x'*80,'\u200b']+list(map(str,range(18)));rows=[(str(i),services[:]) for i in range(100)];before=copy.deepcopy(rows);out=audit_access(services,rows)
    assert out['full_access']==list(map(str,range(100)))
    out['missing'][0][1].append('z');out['full_access'].clear();assert rows==before
    assert audit_access(['\u200b'],[('x'*80,[])])['no_access']==['x'*80]
