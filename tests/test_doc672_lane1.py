from collections import Counter
import itertools
import pytest
from sugarcode.extra_doc.bounded_context672 import audit


def test_complete_ownership_assignments_relational_oracle():
    entities=['a','b','c','d'];calls=list(itertools.product(entities,repeat=2))*2
    for contexts in itertools.product(('x','y','z'),repeat=4):
        owners=dict(zip(entities,contexts));got=audit(owners,calls)
        flags=[owners[a]!=owners[b] for a,b in calls]
        expected=Counter((owners[a],owners[b]) for a,b in calls if owners[a]!=owners[b])
        assert got['same_context']==[i for i,f in enumerate(flags) if not f]
        assert got['cross_context']==[i for i,f in enumerate(flags) if f]
        assert got['context_edges']==[(a,b,expected[a,b]) for a,b in sorted(expected)]
        assert got['boundaries_validated'] is False and got['claim']=='PARTIAL'

class D(dict):pass
class L(list):pass
class T(tuple):pass
class S(str):pass

@pytest.mark.parametrize('owners,calls,message',[
 (D(),[],'owners must be an exact dict with 0..100 entries'),
 ({str(i):'x' for i in range(101)},[],'owners must be an exact dict with 0..100 entries'),
 *[({x:'y'},[],'entity and context IDs must be nonblank strings of 1..80 characters') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ({'a':S('x')},[],'entity and context IDs must be nonblank strings of 1..80 characters'),
 ({},L(),'calls must be an exact list with 0..500 entries'),
 ({'a':'x'},[('a','a')]*501,'calls must be an exact list with 0..500 entries'),
 ({},[T(('a','b'))],'call must be an entity pair tuple'),
 ({'a':'x'},[('a','b')],'call endpoints must be exact known entity IDs'),
 ({'a':'x'},[(S('a'),'a')],'call endpoints must be exact known entity IDs'),
])
def test_invalid(owners,calls,message):
    with pytest.raises(ValueError) as exc:audit(owners,calls)
    assert str(exc.value)==message


def test_maxima_literal_zero_width_and_immutability():
    owners={str(i):'x' for i in range(100)};calls=[('0','99')]*500
    before=repr((owners,calls));assert len(audit(owners,calls)['same_context'])==500
    assert repr((owners,calls))==before
    assert audit({'\u200b':'\u200b'},[('\u200b','\u200b')])['same_context']==[0]
    assert audit({},[])['context_edges']==[]
