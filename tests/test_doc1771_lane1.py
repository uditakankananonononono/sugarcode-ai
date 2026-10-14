import random
import copy
import pytest
from sugarcode.extra_doc.movement1771 import audit_attendance
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_participant_incidence_oracle():
    rng=random.Random(1771)
    for _ in range(100):
        rows=[(str(i),rng.sample(list('abcdef'),rng.randrange(7))) for i in range(10)];matrix=[[int(p in pp) for p in 'abcdef'] for n,pp in rows]
        people=[p for j,p in enumerate('abcdef') if sum(r[j] for r in matrix)>0]
        overlap=[(rows[i][0],rows[i+1][0],sum(a*b for a,b in zip(matrix[i],matrix[i+1]))) for i in range(9)]
        assert audit_attendance(rows)=={'participants':people,'attendance':[(p,sum(pp.count(p) for n,pp in rows)) for p in people],'overlap':overlap,'claim':'PARTIAL','movement_validated':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'events must be an exact list with 1..20 entries') for x in (None,L([('a',[])]),(('a',[]),),[],[(str(i),[]) for i in range(21)])],
 *[([x],'event must be an id participants tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[])],'event IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'event IDs must be unique valid labels'),
 *[([('a',x)],'participants must be an exact list of 0..100 unique valid labels') for x in (None,L(),('a',),['a','a'],list(map(str,range(101))),*[[x] for x in BAD])],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_attendance(rows)
    assert str(exc.value)==message


def test_caps_singleton_empty_and_ownership():
    people=['x'*80,'\u200b']+list(map(str,range(98)));rows=[(str(i),people[:]) for i in range(20)];before=copy.deepcopy(rows);out=audit_attendance(rows)
    assert out['attendance']==[(p,20) for p in sorted(people)] and len(out['overlap'])==19
    for x in out.values():
        if type(x) is list:x.clear()
    assert rows==before
    assert audit_attendance([('x'*80,[])])['participants']==[]
