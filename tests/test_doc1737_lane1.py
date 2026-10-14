import random
import pytest
from sugarcode.extra_doc.cross_cultural1737 import audit


def test_independent_item_count_oracle():
    rng=random.Random(1737)
    for _ in range(100):
        req=list('abc');groups=[(str(i),rng.sample(list('abcd'),rng.randrange(5))) for i in range(10)];got=audit(req,groups)
        assert got['missing']==[(n,[r for r in req if all(r!=x for x in items)]) for n,items in groups]
        assert got['shared']==[x for x in 'abcd' if sum(x in items for n,items in groups)==len(groups)]
        assert got['claim']=='PARTIAL' and got['equivalence_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass
@pytest.mark.parametrize('req,groups,message',[
 (L(['a']),[('a',[]),('b',[])],'requirements must be an exact list with 1..20 entries'),
 ([],[('a',[]),('b',[])],'requirements must be an exact list with 1..20 entries'),
 (list(map(str,range(21))),[('a',[]),('b',[])],'requirements must be an exact list with 1..20 entries'),
 *[([x],[('a',[]),('b',[])],'requirements must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 (['a'],L([('a',[]),('b',[])]),'groups must be an exact list with 2..50 entries'),
 (['a'],[('a',[])],'groups must be an exact list with 2..50 entries'),
 (['a'],[(str(i),[]) for i in range(51)],'groups must be an exact list with 2..50 entries'),
 (['a'],[T(('a',[])),('b',[])],'group must be an id items tuple'),
 (['a'],[('a',[],1),('b',[])],'group must be an id items tuple'),
 (['a'],[(S('a'),[]),('b',[])],'group IDs must be unique valid labels'),
 *[(['a'],[('a',x),('b',[])],'items must be an exact list of 0..20 unique valid labels') for x in (L(),list(map(str,range(21))),[S('a')],['a','a'])],
])
def test_invalid(req,groups,message):
    with pytest.raises(ValueError) as exc:audit(req,groups)
    assert str(exc.value)==message


def test_caps_and_labels():
    req=list(map(str,range(20)));groups=[(str(i),req[:]) for i in range(50)]
    assert audit(req,groups)['shared']==sorted(req)
    assert audit(['x'*80],[('a',['x'*80]),('\u200b',['x'*80])])['missing']==[('a',[]),('\u200b',[])]
