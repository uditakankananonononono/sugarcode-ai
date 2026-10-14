import random
import pytest
from sugarcode.extra_doc.thematic1746 import map_themes
class L(list):pass
class T(tuple):pass
class S(str):pass
BAD=(None,True,1,S('a'),'','\t','\u00a0','\u3000','\u2003','\u0085','x'*81)

@pytest.mark.parametrize('rows,message',[
 *[(x,'themes must be an exact list with 1..20 entries') for x in (None,L([(str(i),['a']) for i in range(1)]),tuple((str(i),['a']) for i in range(1)),[(str(i),['a']) for i in range(0)],[(str(i),['a']) for i in range(21)])],
 *[([x]+[(str(i),['a']) for i in range(1,1)],'themes row must be an id codes tuple') for x in (['a',['a']],T(('a',['a'])),('a',),('a',['a'],1))],
 *[([(x,['a'])]+[(str(i),['a']) for i in range(1,1)],'themes IDs must be unique valid labels') for x in BAD],
 ([('a',['a']),('a',['b'])],'themes IDs must be unique valid labels'),
 *[([('a',x)]+[(str(i),['a']) for i in range(1,1)],'themes codes must be an exact list of 1..20 unique valid labels') for x in (None,L(['a']),('a',),['a','a'],list(map(str,range(21))),*[[x] for x in BAD],[])],
])
def test_invalid(rows,message):
    with pytest.raises(ValueError) as exc:map_themes(rows,[('e',[])])
    assert str(exc.value)==message

def test_independent_code_membership_join():
    rng=random.Random(1746)
    for _ in range(100):
        themes=[(str(i),rng.sample(list('abcdef'),rng.randint(1,6))) for i in range(6)]
        excerpts=[(str(i),rng.sample(list('abcdefg'),rng.randrange(8))) for i in range(30)]
        allcodes=[c for t,cs in themes for c in cs]
        coverage=[(n,[t for t,tc in themes if sum(c in tc for c in cs)>0],sorted(c for c in cs if c not in allcodes)) for n,cs in excerpts]
        counts=[(t,sum(sum(c in tc for c in cs)>0 for n,cs in excerpts)) for t,tc in themes]
        assert map_themes(themes,excerpts)=={'coverage':coverage,'theme_counts':counts,'claim':'PARTIAL','themes_validated':False}

@pytest.mark.parametrize('rows,message',[
 *[(x,'excerpts must be an exact list with 1..100 entries') for x in (L([('e',[])]),[],[(str(i),[]) for i in range(101)])],
 ([T(('e',[]))],'excerpts row must be an id codes tuple'),
 ([('e',[]),('e',[])],'excerpts IDs must be unique valid labels'),
 *[([(x,[])],'excerpts IDs must be unique valid labels') for x in BAD],
 *[([('e',x)],'excerpts codes must be an exact list of 0..20 unique valid labels') for x in (L(),['a','a'],list(map(str,range(21))),*[[x] for x in BAD])],
])
def test_excerpt_invalid(rows,message):
    with pytest.raises(ValueError) as exc:map_themes([('t',['a'])],rows)
    assert str(exc.value)==message

def test_caps():
    codes=['x'*80]+list(map(str,range(19)))
    got=map_themes([(str(i),codes[:]) for i in range(20)],[(str(i),codes[:]) for i in range(100)])
    assert got['theme_counts']==[(str(i),100) for i in range(20)]
    assert map_themes([('x'*80,['\u200b'])],[('e'*80,[])])['coverage']==[('e'*80,[],[])]

@pytest.mark.parametrize('rows,message',[
 ((('e',[]),),'excerpts must be an exact list with 1..100 entries'),
 ([['e',[]]],'excerpts row must be an id codes tuple'),
 ([('e',)],'excerpts row must be an id codes tuple'),
 ([('e',[],1)],'excerpts row must be an id codes tuple'),
 ([('e',('a',))],'excerpts codes must be an exact list of 0..20 unique valid labels'),
 ([('e',None)],'excerpts codes must be an exact list of 0..20 unique valid labels'),
])
def test_excerpt_shapes(rows,message):
    with pytest.raises(ValueError) as exc:map_themes([('t',['a'])],rows)
    assert str(exc.value)==message
