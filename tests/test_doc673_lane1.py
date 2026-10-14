import random
import pytest
from sugarcode.extra_doc.ubiquitous_language673 import audit


def test_independent_group_scan_oracle():
    rng=random.Random(673)
    for _ in range(100):
        rows=[(str(c),str(t),str(rng.randrange(4))) for c in range(4) for t in range(4) if rng.randrange(2)]
        got=audit(rows);conflicts=[];shared=[];aliases=[]
        for term in sorted({r[1] for r in rows}):
            matches=[(c,d) for c,t,d in rows if t==term]
            ds=sorted({d for _,d in matches})
            if len(ds)>1:conflicts.append((term,sorted(matches)))
            elif len(matches)>1:shared.append((term,ds[0],sorted(c for c,_ in matches)))
        for definition in sorted({r[2] for r in rows}):
            ts=sorted({t for _,t,d in rows if d==definition})
            if len(ts)>1:aliases.append((definition,ts))
        assert got['conflicts']==conflicts and got['shared']==shared and got['definition_aliases']==aliases
        assert got['claim']=='PARTIAL' and got['semantic_equivalence_validated'] is False

class L(list):pass
class T(tuple):pass
class S(str):pass

@pytest.mark.parametrize('entries,message',[
 (L(),'entries must be an exact list with 0..100 entries'),
 ([('c',str(i),'d') for i in range(101)],'entries must be an exact list with 0..100 entries'),
 ([T(('c','t','d'))],'entry must be a context, term, definition tuple'),
 *[([tuple(x if i==pos else 'a' for i in range(3))],'fields must be nonblank exact strings of 1..120 characters') for pos in range(3) for x in (S('x'),'\t','\u00a0','\u3000','\u2003','\u0085','x'*121)],
 ([('c','t','d')]*2,'context-term pairs must be unique'),
])
def test_invalid(entries,message):
    with pytest.raises(ValueError) as exc:audit(entries)
    assert str(exc.value)==message


def test_limits_zero_width_order_unchanged():
    rows=[('c',str(i),'d') for i in range(100)];before=repr(rows)
    assert len(audit(rows)['definition_aliases'][0][1])==100
    assert repr(rows)==before
    assert audit([('\u200b','\u200b','\u200b')])['conflicts']==[]
    assert audit([])['shared']==[]
    assert audit([('z','t','d'),('a','t','d')])['shared']==[('t','d',['a','z'])]
