import random
import pytest
from sugarcode.extra_doc.semiotics1750 import audit_signs
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)


def test_independent_meaning_incidence_oracle():
    rng=random.Random(1750)
    for _ in range(100):
        signs=[(str(i),rng.sample(list('abcd'),rng.randint(1,4))) for i in range(10)]
        shared=[(m,sorted(n for n,ms in signs if ms.count(m))) for m in 'abcd' if sum(ms.count(m) for n,ms in signs)>1]
        assert audit_signs(signs)=={'ambiguous':[(n,sorted(ms)) for n,ms in signs if sum(1 for m in ms)>1],'shared_meanings':shared,'claim':'PARTIAL','meaning_validated':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'signs must be an exact list with 1..100 entries') for x in (None,L([('a',['m'])]),(('a',['m']),),[],[(str(i),['m']) for i in range(101)])],
 *[([x],'sign must be an id meanings tuple') for x in (['a',['m']],T(('a',['m'])),('a',),('a',['m'],1))],
 *[([(x,['m'])],'sign IDs must be unique valid labels') for x in BAD],
 ([('a',['m']),('a',['n'])],'sign IDs must be unique valid labels'),
 *[([('a',x)],'meanings must be an exact list of 1..20 unique valid labels') for x in (None,L(['m']),('m',),[],['m','m'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:audit_signs(rows)
    assert str(exc.value)==message


def test_caps_unshared_and_zero_width():
    meanings=['x'*80]+list(map(str,range(19)));got=audit_signs([(str(i),meanings[:]) for i in range(100)])
    assert len(got['ambiguous'])==100 and len(got['shared_meanings'])==20
    assert audit_signs([('x'*80,['\u200b'])])['ambiguous']==[]
    assert audit_signs([('a',['m'])])['shared_meanings']==[]
