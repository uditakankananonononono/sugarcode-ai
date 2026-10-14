import random
import pytest
from sugarcode.extra_doc.institution1761 import audit_rules
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_rule_incidence_oracle():
    rng=random.Random(1761);rules=list('abcd')
    for _ in range(100):
        rng.shuffle(rules);rows=[(str(i),rng.sample(rules,rng.randrange(5))) for i in range(20)]
        matrix=[[int(r in obs) for r in rules] for n,obs in rows]
        assert audit_rules(rules,rows)=={'missing':[(n,[r for j,r in enumerate(rules) if not matrix[i][j]]) for i,(n,obs) in enumerate(rows)],'rule_counts':[(r,sum(row[j] for row in matrix)) for j,r in enumerate(rules)],'claim':'PARTIAL','compliance_validated':False}

@pytest.mark.parametrize('rules',[None,L(['a']),('a',),[],list(map(str,range(21))),['a','a'],*[[x] for x in BAD]])
def test_rules_invalid(rules):
    with pytest.raises(ValueError) as exc:audit_rules(rules,[('i',[])])
    assert str(exc.value)=='rules must be an exact list of 1..20 unique valid labels'

@pytest.mark.parametrize('rows,message',[
 *[(x,'institutions must be an exact list with 1..100 entries') for x in (None,L([('a',[])]),(('a',[]),),[],[(str(i),[]) for i in range(101)])],
 *[([x],'institution must be an id observed_rules tuple') for x in (['a',[]],T(('a',[])),('a',),('a',[],1))],
 *[([(x,[])],'institution IDs must be unique valid labels') for x in BAD],
 ([('a',[]),('a',[])],'institution IDs must be unique valid labels'),
 *[([('a',x)],'observed must be an exact list of 0..20 unique known rule labels') for x in (None,L(),('a',),['a','a'],['unknown'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_rows_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_rules(['a','b'],rows)
    assert str(exc.value)==message


def test_caps_complete_empty_and_zero_width():
    rules=['x'*80]+list(map(str,range(19)));got=audit_rules(rules,[(str(i),rules[:]) for i in range(100)])
    assert got['rule_counts']==[(r,100) for r in rules] and all(not missing for n,missing in got['missing'])
    assert audit_rules(['\u200b'],[('x'*80,[])])['missing']==[('x'*80,['\u200b'])]
