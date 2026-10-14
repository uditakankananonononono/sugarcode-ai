import random
import pytest
from sugarcode.extra_doc.grounded1747 import track_codes
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)

@pytest.mark.parametrize('rows,message',[
 *[(x,'rounds must be an exact list with 2..20 entries') for x in (None,L([(str(i),['a']) for i in range(2)]),tuple((str(i),['a']) for i in range(2)),[(str(i),['a']) for i in range(1)],[(str(i),['a']) for i in range(21)])],
 *[([x]+[(str(i),['a']) for i in range(1,2)],'round must be an id codes tuple') for x in (['a',['a']],T(('a',['a'])),('a',),('a',['a'],1))],
 *[([(x,['a'])]+[(str(i),['a']) for i in range(1,2)],'round IDs must be unique valid labels') for x in BAD],
 ([('a',['a']),('a',['b'])],'round IDs must be unique valid labels'),
 *[([('a',x)]+[(str(i),['a']) for i in range(1,2)],'codes must be an exact list of 0..100 unique valid labels') for x in (None,L(['a']),('a',),['a','a'],list(map(str,range(101))),*[[x] for x in BAD])],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:track_codes(rows)
    assert str(exc.value)==message

def test_independent_first_occurrence_join():
    rng=random.Random(1747)
    for _ in range(100):
        rounds=[(str(i),rng.sample(list('abcdef'),rng.randrange(7))) for i in range(8)]
        codes=sorted({c for n,cs in rounds for c in cs});first={c:next(i for i,(n,cs) in enumerate(rounds) if c in cs) for c in codes}
        new=[(n,[c for c in codes if first[c]==i]) for i,(n,cs) in enumerate(rounds)]
        assert track_codes(rounds)=={'new_codes':new,'first_seen':[(c,rounds[first[c]][0]) for c in codes],'no_new_code_rounds':[n for n,cs in new if not cs],'claim':'PARTIAL','theory_validated':False,'saturation_claimed':False}

def test_caps_and_disappeared_code_not_new():
    codes=['x'*80]+list(map(str,range(99)))
    got=track_codes([(str(i),codes[:]) for i in range(20)])
    assert got['new_codes'][0]==('0',sorted(codes)) and got['new_codes'][1]==('1',[])
    assert track_codes([('x'*80,['\u200b']),('b',[]),('c',['\u200b'])])['new_codes']==[('x'*80,['\u200b']),('b',[]),('c',[])]
