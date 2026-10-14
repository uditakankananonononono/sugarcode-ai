import itertools
import pytest
from sugarcode.extra_doc.anti_corruption678 import translate


def test_independent_relational_join_oracle():
    rules={'x':'a','y':'b','z':'c'}
    for bits in itertools.product((False,True),repeat=4):
        payload={k:k*2 for k,b in zip('wxyz',bits) if b};before=repr(payload)
        got=translate(rules,payload)
        mapped={inner:v for outer,inner in rules.items() for k,v in payload.items() if k==outer}
        unknown={k:v for k,v in payload.items() if all(k!=outer for outer in rules)}
        missing=[outer for outer in rules if all(outer!=k for k in payload)]
        assert got['mapped']==mapped and got['unknown']==unknown and got['missing']==missing
        assert got['claim']=='PARTIAL' and got['semantics_validated'] is False
        assert repr(payload)==before

class D(dict):pass
class S(str):pass

@pytest.mark.parametrize('rules,payload,message',[
 (D(x='a'),{},'rules must be an exact dict with 1..20 entries'),
 ({},{},'rules must be an exact dict with 1..20 entries'),
 *[({x:'a'},{},'rule IDs must be nonblank exact strings of 1..80 characters') for x in (S('x'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 ({'x':'a','y':'a'},{},'internal IDs must be distinct'),
 ({'x':'a'},D(),'payload must be an exact dict with 0..50 entries'),
 *[({'x':'a'},{x:''},'payload IDs must be nonblank exact strings of 1..80 characters') for x in (S('x'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*81)],
 *[({'x':'a'},{'x':x},'payload values must be exact strings with 0..120 characters') for x in (S('x'),None,'x'*121)],
])
def test_invalid(rules,payload,message):
    with pytest.raises(ValueError) as exc:translate(rules,payload)
    assert str(exc.value)==message


def test_bounds_and_literal_zero_width():
    rules={str(i):'x'+str(i) for i in range(20)};payload={str(i):'v'*120 for i in range(50)}
    assert len(translate(rules,payload)['mapped'])==20 and len(translate(rules,payload)['unknown'])==30
    assert translate({'\u200b':'x'*80},{'\u200b':''})['mapped']=={'x'*80:''}
