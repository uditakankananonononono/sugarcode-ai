import random
import pytest
from sugarcode.extra_doc.hexagonal679 import audit


def test_independent_binding_count_oracle():
    rng=random.Random(679)
    for _ in range(100):
        ports=['a','b','c'];rows=[(rng.choice('abcd'),rng.choice('xyz')) for _ in range(20)]
        expected={p:sorted({a for q,a in rows if q==p}) for p in ports}
        got=audit(ports,rows)
        assert got['unbound']==[p for p in ports if not expected[p]]
        assert got['multiple']==[(p,expected[p]) for p in ports if len(expected[p])>1]
        assert got['unknown']==[i for i,r in enumerate(rows) if r[0] not in ports]
        assert got['duplicates']==[i for i,r in enumerate(rows) if r in rows[:i]]
        assert got['claim']=='PARTIAL' and got['wiring_validated'] is False

class L(list):pass
class S(str):pass
class T(tuple):pass

@pytest.mark.parametrize('ports,rows,message',[
 (L(),[],'ports must be an exact list with 0..50 entries'),
 (['a']*2,[],'ports must be unique valid labels'),
 *[([x],[],'ports must be unique valid labels') for x in (S('a'),'\t','\u00a0','\u3000','\u2003','\u0085','a'*81)],
 ([],L(),'bindings must be an exact list with 0..100 entries'),
 ([],[T(('a','b'))],'bindings must be valid port adapter tuples'),
 ([],[('a',S('b'))],'bindings must be valid port adapter tuples'),
])
def test_invalid(ports,rows,message):
    with pytest.raises(ValueError) as exc:audit(ports,rows)
    assert str(exc.value)==message


def test_maxima_zero_width():
    ports=[str(i) for i in range(50)];bindings=[(p,'x'*80) for p in ports]*2
    assert audit(ports,bindings)['duplicates']==list(range(50,100))
    assert audit(['\u200b'],[('\u200b','a')])['unbound']==[]
